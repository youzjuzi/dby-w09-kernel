#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Replay the patch and exercise the actual transport functions with host stubs."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT.parent / 'upstream/linux-7.2.10'


def function(source, name):
    start = re.search(r'^(?:static )?int ' + name + r'\(', source, re.M).start()
    return source[start:source.index('\n}', start) + 2]


class VoteHandle(unittest.TestCase):
    def test_replay_and_transport(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            directory = tmp / 'sound/soc/qcom/qdsp6'
            directory.mkdir(parents=True)
            for name in ('q6afe.h', 'q6afe.c', 'q6afe-dai.c'):
                shutil.copyfile(UPSTREAM / 'sound/soc/qcom/qdsp6' / name, directory / name)
            for number in ('0009', '0021'):
                patch = next((ROOT / 'patches').glob(number + '-*'))
                result = subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-d', str(tmp),
                                         '-i', str(patch)], check=True, capture_output=True, text=True)
                self.assertNotIn('offset', result.stdout)
                self.assertNotIn('fuzz', result.stdout)
            source = (directory / 'q6afe.c').read_text()
            callback = function(source, 'q6afe_callback')
            response = callback.split('case AFE_CMD_RSP_REMOTE_LPASS_CORE_HW_VOTE_REQUEST:')[1]
            self.assertLess(response.index('payload_size < sizeof(u32)'), response.index('payload[0]'))
            self.assertNotIn('res->status', response)
            for command in ('VOTE', 'DEVOTE'):
                self.assertIn('case AFE_CMD_REMOTE_LPASS_CORE_HW_' + command + '_REQUEST:', callback)
            vote = function(source, 'q6afe_vote_lpass_core_hw')
            self.assertLess(vote.index('mutex_lock'), vote.index('*client_handle ='))
            self.assertLess(vote.index('*client_handle ='), vote.index('mutex_unlock'))
            unvote = function(source, 'q6afe_unvote_lpass_core_hw')
            self.assertIn('afe_apr_send_pkt(afe, pkt, NULL,', unvote)
            self.assertIn('dev_dbg_once', unvote)
            # Extract definitions and functions, rather than duplicating their logic.
            defines = '\n'.join(line for line in source.splitlines()
                                if re.match(r'#define (AFE_.*(?:REQUEST|PARAM_V2|STOP|START|SET_PARAM)|AFE_CLK_TOKEN|TIMEOUT_MS)\s', line))
            structs = '\n'.join(re.search(r'struct ' + name + r' \{.*?\} __packed;', source, re.S)[0]
                                for name in ('afe_cmd_remote_lpass_core_hw_vote_request',
                                             'afe_cmd_remote_lpass_core_hw_devote_request'))
            functions = '\n\n'.join(function(source, name) for name in (
                'q6afe_callback', '__afe_apr_send_pkt', 'afe_apr_send_pkt',
                'q6afe_unvote_lpass_core_hw', 'q6afe_vote_lpass_core_hw'))
            harness = tmp / 'transport.c'
            harness.write_text(STUBS + '\n' + defines + '\n' + structs + '\n' + functions + '\n' + SCENARIOS)
            binary = tmp / 'transport'
            subprocess.run(['cc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                            '-Wno-unused-parameter', str(harness), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True)


STUBS = r'''
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>
typedef uint32_t u32;
typedef uint16_t u16;
typedef int wait_queue_head_t;
#define __packed __attribute__((packed))
static void free_ptr(void *p) { free(*(void **)p); }
#define __free(x) __attribute__((cleanup(free_ptr)))
#define GFP_KERNEL 0
static int fail_alloc;
static void *kzalloc(size_t n, int flag) { return fail_alloc ? NULL : calloc(1, n); }
#define dev_err(...) ((void)0)
#define dev_dbg_once(...) ((void)0)
#define APR_BASIC_RSP_RESULT 0x110e8
#define APR_HDR_FIELD(...) 0
#define APR_HDR_SIZE sizeof(struct apr_hdr)
#define msecs_to_jiffies(x) (x)
#define smp_store_release(p, v) __atomic_store_n(p, v, __ATOMIC_RELEASE)
#define smp_load_acquire(p) __atomic_load_n(p, __ATOMIC_ACQUIRE)
struct device { struct device *parent; void *data; };
struct apr_device { struct device dev; };
struct apr_hdr { u32 hdr_field, pkt_size, src_port, dest_port, token, opcode; };
struct apr_pkt { struct apr_hdr hdr; };
struct apr_resp_pkt { struct apr_hdr hdr; size_t payload_size; void *payload; };
struct aprv2_ibasic_rsp_result_t { u32 opcode, status; };
struct q6afe { struct apr_device *apr; struct device *dev; int lock;
    struct aprv2_ibasic_rsp_result_t result; u32 client_handle; wait_queue_head_t wait; };
struct q6afe_port { struct aprv2_ibasic_rsp_result_t result; int wait, refcount; };
static struct q6afe *instance;
static int unlock_clobber;
static void mutex_lock(int *m) { assert(!*m); *m = 1; }
static void mutex_unlock(int *m) {
    assert(*m); *m = 0;
    /* Model a new transaction starting as soon as the mutex is released. */
    if (unlock_clobber) instance->client_handle = 0xdead;
}
#define lockdep_assert_held(m) assert(*(m))
static void *dev_get_drvdata(struct device *d) { return d->data; }
static struct q6afe_port *q6afe_find_port(struct q6afe *a, int t) { return NULL; }
static void q6afe_port_free(void) { }
static void kref_put(int *r, void (*fn)(void)) { }
static void wake_up(int *w) { ++*w; }
static void strscpy(char *d, const char *s, size_t n) { strncpy(d, s, n); }
static int apr_send_pkt(struct apr_device *dev, struct apr_pkt *pkt);
static void deliver(void);
static int waits;
#define wait_event_timeout(w, condition, timeout) \
    ({ (void)(w); (void)(timeout); ++waits; deliver(); (condition) ? 1 : 0; })
'''

SCENARIOS = r'''
enum mode { HANDLE, ZERO, DSP_ERROR, TIMEOUT, SHORT, SEND_ERROR, BASIC_OK };
static enum mode mode;
static int sends;
static u32 request, token, response_handle, sent_handle;
static struct apr_device adev;
static int apr_send_pkt(struct apr_device *dev, struct apr_pkt *pkt) {
    assert(instance->lock);
    ++sends; request = pkt->hdr.opcode; token = pkt->hdr.token;
    if (request == AFE_CMD_REMOTE_LPASS_CORE_HW_DEVOTE_REQUEST) {
        struct afe_cmd_remote_lpass_core_hw_devote_request *p = (void *)pkt + APR_HDR_SIZE;
        sent_handle = p->client_handle;
        assert(p->hw_block_id == token);
    }
    return mode == SEND_ERROR ? -EIO : (int)pkt->hdr.pkt_size;
}
static void respond(u32 opcode, void *payload, size_t size) {
    struct apr_resp_pkt rsp = { .hdr = { .opcode = opcode, .token = token },
                               .payload = payload, .payload_size = size };
    q6afe_callback(&adev, &rsp);
}
static void deliver(void) {
    assert(instance->lock);
    if (mode == TIMEOUT) return;
    if (mode == DSP_ERROR || mode == BASIC_OK ||
        request == AFE_CMD_REMOTE_LPASS_CORE_HW_DEVOTE_REQUEST) {
        struct aprv2_ibasic_rsp_result_t res = { request, mode == DSP_ERROR ? 1 : 0 };
        respond(APR_BASIC_RSP_RESULT, &res, sizeof(res));
    } else {
        /* Exactly four accessible bytes: reading a basic-result status faults. */
        size_t page = sysconf(_SC_PAGESIZE);
        char *map = mmap(NULL, 2 * page, PROT_READ | PROT_WRITE,
                         MAP_PRIVATE | MAP_ANONYMOUS, -1, 0);
        assert(map != MAP_FAILED);
        assert(!mprotect(map + page, page, PROT_NONE));
        u32 *p = (void *)(map + page - sizeof(u32));
        *p = mode == ZERO ? 0 : response_handle;
        respond(AFE_CMD_RSP_REMOTE_LPASS_CORE_HW_VOTE_REQUEST, p,
                mode == SHORT ? 3 : sizeof(*p));
        assert(!munmap(map, 2 * page));
    }
}
int main(void) {
    struct q6afe afe = { .apr = &adev, .dev = &adev.dev };
    struct device child = { .parent = &adev.dev };
    instance = &afe; adev.dev.data = &afe;
    u32 handle = 77;
    unlock_clobber = 1;
    for (u32 block = 2; block <= 4; ++block) {
        for (int cycle = 0; cycle < 5; ++cycle) {
            mode = HANDLE; response_handle = 100 + block * 5 + cycle;
            assert(!q6afe_vote_lpass_core_hw(&child, block, "test", &handle));
            assert(handle == response_handle && !afe.lock);
            int before = waits;
            assert(!q6afe_unvote_lpass_core_hw(&child, block, handle));
            assert(waits == before + 1 && sent_handle == handle && !afe.lock);
        }
    }
    for (int m = ZERO; m <= BASIC_OK; ++m) {
        mode = m; handle = 77;
        int expected = (m == TIMEOUT || m == SHORT || m == BASIC_OK) ? -ETIMEDOUT : -EINVAL;
        assert(q6afe_vote_lpass_core_hw(&child, 3, "test", &handle) == expected);
        assert(handle == 77 && !afe.lock);
    }
    mode = DSP_ERROR;
    assert(q6afe_unvote_lpass_core_hw(&child, 3, 77) == -EINVAL);
    mode = TIMEOUT;
    assert(q6afe_unvote_lpass_core_hw(&child, 3, 77) == -ETIMEDOUT);
    mode = SEND_ERROR;
    assert(q6afe_unvote_lpass_core_hw(&child, 3, 77) == -EINVAL);
    int before = sends;
    assert(!q6afe_unvote_lpass_core_hw(&child, 3, 0) && sends == before);
    fail_alloc = 1; handle = 77;
    assert(q6afe_vote_lpass_core_hw(&child, 3, "test", &handle) == -ENOMEM);
    assert(handle == 77 && !afe.lock);
    assert(q6afe_unvote_lpass_core_hw(&child, 3, 77) == -ENOMEM);
    assert(!q6afe_unvote_lpass_core_hw(&child, 3, 0));
    /* Both callbacks reject truncated payloads without accessing their data. */
    for (unsigned size = 0; size < 8; ++size) {
        afe.result.opcode = 0; afe.wait = 0;
        respond(APR_BASIC_RSP_RESULT, NULL, size);
        assert(!afe.result.opcode && !afe.wait);
        if (size < 4) {
            respond(AFE_CMD_RSP_REMOTE_LPASS_CORE_HW_VOTE_REQUEST, NULL, size);
            assert(!afe.result.opcode && !afe.wait);
        }
    }
    return 0;
}
'''

if __name__ == '__main__':
    unittest.main()
