#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Replay the Type-C patch and fault-test its actual wake lifecycle on the host."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT.parent / 'upstream/linux-7.2.10'
DIRECTORY = Path('drivers/usb/typec/tcpm/qcom')
FILES = ('qcom_pmic_typec.c', 'qcom_pmic_typec_port.c', 'qcom_pmic_typec_port.h')


def function(text, name):
    pos = text.index(name + '(')
    start = text.rfind('\n', 0, pos) + 1
    begin = text.index('{', pos)
    depth = 1
    end = begin + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


MOCK = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#define BIT(n) (1UL << (n))
#define PMIC_TYPEC_CC_STATE_IRQ 2
#define PMIC_TYPEC_VBUS_IRQ 4
#define PMIC_TYPEC_ATTACH_DETACH_IRQ 5
#define DEFINE_SIMPLE_DEV_PM_OPS(name, suspend, resume)
struct device { bool wake; void *data; };
struct pmic_typec_port_irq_data { int virq, irq; };
struct pmic_typec_port {
    struct device *dev;
    unsigned int nr_irqs;
    struct pmic_typec_port_irq_data *irq_data;
    unsigned long wake_irqs;
};
struct pmic_typec { struct pmic_typec_port *pmic_typec_port; };
static int depth[7], enables[7], disables[7], logs;
static int fail_enable, fail_disable, fail_init, fail_action;
static void (*action)(void *);
static void *action_data;
#define dev_err(...) (++logs)
static void *dev_get_drvdata(struct device *d) { return d->data; }
static bool device_may_wakeup(struct device *d) { return d->wake; }
static int device_init_wakeup(struct device *d, bool enabled)
{
    d->wake = enabled;
    return enabled ? fail_init : 0;
}
static int devm_add_action_or_reset(struct device *d, void (*fn)(void *), void *data)
{
    (void)d;
    if (fail_action) { fn(data); return fail_action; }
    action = fn; action_data = data;
    return 0;
}
static int enable_irq_wake(int irq)
{
    int i = irq - 100;
    assert(i == 1 || i == 3 || i == 4);
    enables[i]++;
    if (i == fail_enable) return -22;
    assert(depth[i]++ == 0);
    return 0;
}
static int disable_irq_wake(int irq)
{
    int i = irq - 100;
    assert(i == 1 || i == 3 || i == 4);
    disables[i]++;
    if (i == fail_disable) return -5;
    assert(depth[i]-- == 1);
    return 0;
}
'''

HARNESS = r'''
static const int wake_indexes[] = {1, 3, 4};
static struct device dev;
static struct pmic_typec_port_irq_data irqs[7];
static struct pmic_typec_port port;
static struct pmic_typec tcpm;
static void reset(void)
{
    memset(depth, 0, sizeof(depth));
    memset(enables, 0, sizeof(enables));
    memset(disables, 0, sizeof(disables));
    for (int i = 0; i < 7; i++) irqs[i] = (struct pmic_typec_port_irq_data){i + 1, i + 100};
    port = (struct pmic_typec_port){&dev, 7, irqs, 0};
    tcpm.pmic_typec_port = &port;
    dev = (struct device){false, &tcpm};
    fail_enable = fail_disable = -1;
    fail_init = fail_action = logs = 0;
    action = NULL; action_data = NULL;
}
static void empty(void)
{
    assert(port.wake_irqs == 0);
    for (int i = 0; i < 7; i++) assert(depth[i] == 0);
}
int main(void)
{
    reset();
    assert(!qcom_pmic_typec_port_init_wakeup(&port));
    assert(dev.wake && action);
    for (int i = 0; i < 7; i++) assert(!enables[i]);
    for (int n = 0; n < 3; n++) {
        assert(!qcom_pmic_typec_port_suspend(&dev));
        assert(port.wake_irqs == (BIT(1) | BIT(3) | BIT(4)));
        assert(!qcom_pmic_typec_port_suspend(&dev)); /* no double reference */
        assert(!qcom_pmic_typec_port_resume(&dev));
        assert(!qcom_pmic_typec_port_resume(&dev));
        empty();
    }
    assert(enables[1] == 3 && enables[3] == 3 && enables[4] == 3);
    assert(disables[1] == 3 && disables[3] == 3 && disables[4] == 3);
    dev.wake = false;
    assert(!qcom_pmic_typec_port_suspend(&dev));
    assert(!qcom_pmic_typec_port_resume(&dev));
    assert(enables[1] == 3 && enables[3] == 3 && enables[4] == 3);
    action(action_data); assert(!dev.wake); empty();

    for (int n = 0; n < 3; n++) {
        int i = wake_indexes[n];
        reset(); dev.wake = true; fail_enable = i;
        assert(qcom_pmic_typec_port_suspend(&dev) == -22);
        assert(logs == 1); empty();
        assert(disables[1] == (i > 1));
        assert(disables[3] == (i > 3));
        assert(!disables[4]);
    }
    reset(); dev.wake = true; fail_enable = 4; fail_disable = 1;
    assert(qcom_pmic_typec_port_suspend(&dev) == -22);
    assert(port.wake_irqs == BIT(1) && depth[1] == 1 && logs == 2);
    fail_enable = fail_disable = -1;
    assert(!qcom_pmic_typec_port_suspend(&dev));
    assert(enables[1] == 1); /* retained bit is not enabled twice */
    assert(!qcom_pmic_typec_port_resume(&dev)); empty();

    for (int n = 0; n < 3; n++) {
        int i = wake_indexes[n];
        reset(); dev.wake = true;
        assert(!qcom_pmic_typec_port_suspend(&dev));
        fail_disable = i;
        assert(qcom_pmic_typec_port_resume(&dev) == -5);
        assert(port.wake_irqs == BIT(i) && logs == 1);
        assert(disables[1] == 1 && disables[3] == 1 && disables[4] == 1);
        fail_disable = -1;
        assert(!qcom_pmic_typec_port_resume(&dev)); empty();
    }
    reset(); assert(!qcom_pmic_typec_port_init_wakeup(&port));
    assert(!qcom_pmic_typec_port_suspend(&dev));
    dev.wake = false; /* a policy change must not leak armed references */
    assert(!qcom_pmic_typec_port_resume(&dev)); empty();
    action(action_data); assert(!dev.wake);

    reset(); fail_init = -12;
    assert(qcom_pmic_typec_port_init_wakeup(&port) == -12);
    assert(!dev.wake && !action); empty();
    reset(); fail_action = -12;
    assert(qcom_pmic_typec_port_init_wakeup(&port) == -12);
    assert(!dev.wake && !action); empty();
    reset(); assert(!qcom_pmic_typec_port_init_wakeup(&port));
    action(action_data); assert(!dev.wake); empty(); /* later probe failure */
    reset(); assert(!qcom_pmic_typec_port_init_wakeup(&port));
    assert(!qcom_pmic_typec_port_suspend(&dev));
    fail_disable = 4;
    action(action_data); assert(!dev.wake && port.wake_irqs == BIT(4) && logs == 1);
    fail_disable = -1;
    action(action_data); empty();
    puts("PASS: default wake, policy, IRQ allowlist, cycles, faults, rollback and cleanup");
}
'''


class TypecWake(unittest.TestCase):
    def test_replay_and_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            directory = root / DIRECTORY
            directory.mkdir(parents=True)
            for name in FILES:
                shutil.copyfile(UPSTREAM / DIRECTORY / name, directory / name)
            patch = ROOT / 'patches/0016-usb-typec-qcom-pmic-typec-wake-on-attach.patch'
            result = subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-d', tmp,
                                     '-i', str(patch)], check=True, capture_output=True, text=True)
            self.assertNotIn('offset', result.stdout)
            text = (directory / 'qcom_pmic_typec_port.c').read_text()
            original = (UPSTREAM / DIRECTORY / 'qcom_pmic_typec_port.c').read_text()
            for name in ('pmic_typec_port_isr', 'qcom_pmic_typec_port_cc_debounce',
                         'qcom_pmic_typec_port_start', 'qcom_pmic_typec_port_stop'):
                self.assertEqual(function(text, name), function(original, name))
            self.assertIn('.pm = pm_sleep_ptr(&qcom_pmic_typec_port_pm_ops)',
                          (directory / 'qcom_pmic_typec.c').read_text())
            self.assertIn('return qcom_pmic_typec_port_init_wakeup(pmic_typec_port);',
                          function(text, 'qcom_pmic_typec_port_probe'))
            start = text.index('static int qcom_pmic_typec_port_clear_wake(')
            end = text.index('int qcom_pmic_typec_port_probe(', start)
            source = root / 'wake-test.c'
            source.write_text(MOCK + text[start:end] + HARNESS)
            binary = root / 'wake-test'
            subprocess.run(['cc', '-std=c11', '-O2', '-Wall', '-Wextra', '-Werror',
                            '-fsanitize=undefined', '-fno-sanitize-recover=all',
                            str(source), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


if __name__ == '__main__':
    unittest.main()
