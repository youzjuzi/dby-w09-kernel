#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Replay patches and execute actual panel power functions with fake regulators."""
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT.parent / 'upstream/linux-7.2.10'
SOURCE = Path('drivers/gpu/drm/panel/panel-novatek-nt36523.c')
BINDING = Path('Documentation/devicetree/bindings/display/panel/novatek,nt36523.yaml')


def replay(work, numbers=('0001', '0002', '0003', '0011', '0013', '0014', '0018')):
    for name in (SOURCE, BINDING):
        dest = work / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(UPSTREAM / name, dest)
    for number in numbers:
        patch = next((ROOT / 'patches').glob(number + '-*.patch'))
        result = subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-d', str(work),
                                 '-i', str(patch)], capture_output=True, text=True, check=True)
        assert 'offset' not in result.stdout and 'fuzz' not in result.stdout
    return (work / SOURCE).read_text()


class PanelPower(unittest.TestCase):
    def test_esd_event_recovery_with_fake_drm_and_gpio(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            source = replay(work)
            first = source.index('static void nt36523_esd_queue')
            last = source.index('static int elish_boe_init_sequence')
            functions = source[first:last]
            harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#define ESD_DEBOUNCE_MS 1000
#define ESD_LIMIT 5
#define HZ 1000
#define ESD_WINDOW (60 * HZ)
#define READ_ONCE(x) (x)
#define container_of(p,t,m) ((t *)((char *)(p)-offsetof(t,m)))
#define to_delayed_work(p) container_of(p,struct delayed_work,work)
#define time_before(a,b) ((long)((a)-(b)) < 0)
#define msecs_to_jiffies(x) (x)
#define IS_ERR(p) ((long)(p)<0 && (long)(p)>-4096)
#define PTR_ERR(p) ((int)(long)(p))
#define GPIOD_IN 1
#define IRQF_TRIGGER_RISING 1
#define IRQF_TRIGGER_FALLING 2
#define IRQ_HANDLED 1
#define dev_name(p) "fake-panel"
#define spin_lock_irqsave(p,f) do { (f)=0; assert(!*(p)); *(p)=1; } while (0)
#define spin_unlock_irqrestore(p,f) do { (void)(f); assert(*(p)); *(p)=0; } while (0)
typedef int irqreturn_t;
struct work_struct { int unused; };
struct delayed_work { struct work_struct work; unsigned long due; bool queued; };
struct device { void *of_node; };
struct drm_panel { struct device *dev; };
struct drm_modeset_acquire_ctx { int locks; };
struct drm_crtc_state { bool active; };
struct drm_crtc { struct drm_crtc_state *state; };
struct drm_connector_state { struct drm_crtc *crtc; };
struct drm_connector { struct drm_connector_state *state; };
struct drm_encoder { void *dev; };
struct drm_bridge { struct drm_encoder *encoder; };
struct gpio_desc { int value, irq; };
struct gpio_descs { unsigned int ndescs; struct gpio_desc *desc[2]; };
struct panel_info {
 struct drm_panel panel;
 struct gpio_descs *esd_gpios;
 struct delayed_work esd_work;
 int esd_lock, esd_irqs[2];
 bool esd_ready, esd_enabled, esd_stopping;
 unsigned long esd_deadline, esd_attempts[ESD_LIMIT], esd_resume;
 unsigned int esd_count;
 bool esd_limited;
};
static struct panel_info p;
static struct device dev;
static struct drm_crtc_state cs;
static struct drm_crtc crtc;
static struct drm_connector_state cons;
static struct drm_connector con;
static struct drm_encoder enc;
static struct drm_bridge bridge;
static struct gpio_desc pins[2];
static struct gpio_descs gpios;
static unsigned long jiffies;
static bool esd_recovery, bridge_missing, bridge_dead, lock_edge, lock_off;
static int system_dfl_wq, resets, calls, refs, entered, ctxs, backoffs, mode_locks;
static int lock_deadlocks, reset_deadlocks, reset_error, gives, woulds, done;
static int requests, freed, gpio_puts, irq_fail, gpio_fail, warnings, monitoring;
static void nt36523_esd_queue(struct panel_info *pinfo);
static void log_event(const char *fmt) {
 if (strstr(fmt,"giving up")) gives++;
 if (strstr(fmt,"would reset")) woulds++;
 if (strstr(fmt,"reset done")) done++;
 if (strstr(fmt,"monitoring 2")) monitoring++;
}
#define dev_info(d,fmt,...) log_event(fmt)
#define dev_warn(...) (++warnings)
static void mod_delayed_work(int q,struct delayed_work *w,unsigned long delay) {
 (void)q; w->queued=true;w->due=jiffies+delay;
}
static struct drm_bridge *of_drm_find_and_get_bridge(void *node) {
 (void)node;if(bridge_missing)return NULL;refs++;return &bridge;
}
static void drm_bridge_put(struct drm_bridge *b) {(void)b;assert(refs==1);refs--;}
static bool drm_bridge_enter(struct drm_bridge *b,int *idx) {
 (void)b;*idx=0;if(bridge_dead)return false;entered++;return true;
}
static void drm_bridge_exit(int idx) {(void)idx;assert(entered==1);entered--;}
static void drm_modeset_acquire_init(struct drm_modeset_acquire_ctx *c,int flags) {
 (void)flags;c->locks=0;ctxs++;
}
static int drm_modeset_lock_all_ctx(void *d,struct drm_modeset_acquire_ctx *c) {
 (void)d;if(lock_edge){lock_edge=false;nt36523_esd_queue(&p);}
 if(lock_off){lock_off=false;p.esd_enabled=false;}
 if(lock_deadlocks){lock_deadlocks--;return -EDEADLK;}
 c->locks=1;mode_locks=1;return 0;
}
static void drm_modeset_drop_locks(struct drm_modeset_acquire_ctx *c) {c->locks=mode_locks=0;}
static void drm_modeset_acquire_fini(struct drm_modeset_acquire_ctx *c) {assert(!c->locks);ctxs--;}
static int drm_modeset_backoff(struct drm_modeset_acquire_ctx *c) {
 c->locks=mode_locks=0;backoffs++;return 0;
}
static int gpiod_get_value_cansleep(struct gpio_desc *g) {assert(mode_locks);return g->value;}
static struct drm_connector *drm_atomic_get_connector_for_encoder(struct drm_encoder *e,
 struct drm_modeset_acquire_ctx *c) {(void)e;assert(c->locks);return &con;}
static int drm_bridge_helper_reset_crtc(struct drm_bridge *b,struct drm_modeset_acquire_ctx *c) {
 (void)b;assert(c->locks && p.esd_enabled && cs.active);calls++;
 if(reset_deadlocks){reset_deadlocks--;return -EDEADLK;}
 if(reset_error)return reset_error;
 resets++;
 /* Model non-waiting disable, then enable scheduling while this work runs. */
 p.esd_enabled=false;p.esd_work.queued=false;
 p.esd_enabled=true;nt36523_esd_queue(&p);return 0;
}
static struct gpio_descs *devm_gpiod_get_array_optional(struct device *d,const char *n,int f) {
 (void)d;assert(!strcmp(n,"esd") && f==GPIOD_IN);
 return gpio_fail ? (struct gpio_descs *)(long)gpio_fail : &gpios;
}
static int gpiod_to_irq(struct gpio_desc *g) {return g->irq;}
static int devm_request_irq(struct device *d,int irq,irqreturn_t (*fn)(int,void *),
 unsigned long flags,const char *name,void *data) {
 (void)d;(void)irq;(void)name;assert(flags==3);requests++;
 fn(irq,data); /* An IRQ during setup cannot queue until both requests succeed. */
 assert(!p.esd_work.queued);
 return requests==irq_fail ? -EBUSY : 0;
}
static void devm_free_irq(struct device *d,int irq,void *data) {(void)d;(void)irq;(void)data;freed++;}
static void devm_gpiod_put_array(struct device *d,struct gpio_descs *g) {(void)d;(void)g;gpio_puts++;}
'''
            harness += functions + r'''
static void setup(void) {
 memset(&p,0,sizeof(p));dev.of_node=&dev;p.panel.dev=&dev;
 pins[0]=(struct gpio_desc){1,10};pins[1]=(struct gpio_desc){1,11};
 gpios=(struct gpio_descs){2,{&pins[0],&pins[1]}};p.esd_gpios=&gpios;
 p.esd_ready=p.esd_enabled=true;
 cs.active=true;crtc.state=&cs;cons.crtc=&crtc;con.state=&cons;enc.dev=&dev;bridge.encoder=&enc;
 jiffies=0;esd_recovery=true;bridge_missing=bridge_dead=lock_edge=lock_off=false;
 resets=calls=refs=entered=ctxs=backoffs=mode_locks=lock_deadlocks=reset_deadlocks=reset_error=0;
 gives=woulds=done=requests=freed=gpio_puts=irq_fail=gpio_fail=warnings=monitoring=0;
}
static void run(void) {
 p.esd_work.queued=false;nt36523_esd_work(&p.esd_work.work);
 assert(!refs && !entered && !ctxs && !mode_locks && !p.esd_lock);
}
int main(void) {
 setup();nt36523_esd_irq(10,&p);assert(p.esd_work.due==1000);
 jiffies=900;nt36523_esd_irq(11,&p);assert(p.esd_work.due==1900);
 jiffies=1000;run();assert(!resets && p.esd_work.due==1900);
 jiffies=1900;run();assert(resets==1 && p.esd_work.due==2900);
 for(int i=0;i<2;i++)for(int v=-EIO;v<=0;v+=EIO) {
  setup();pins[i].value=v;run();assert(!calls && !p.esd_count);
 }
 setup();p.esd_enabled=false;nt36523_esd_irq(10,&p);run();assert(!calls && !p.esd_work.queued);
 setup();p.esd_stopping=true;run();assert(!calls);
 setup();p.esd_ready=false;run();assert(!calls);
 setup();bridge_missing=true;run();assert(!calls);
 setup();bridge_dead=true;run();assert(!calls);
 setup();bridge.encoder=NULL;run();assert(!calls);
 setup();cons.crtc=NULL;run();assert(!calls);
 setup();cs.active=false;run();assert(!calls);
 setup();con.state=NULL;run();assert(!calls);
 setup();esd_recovery=false;run();assert(!calls && woulds==1 && !p.esd_count && !p.esd_work.queued);
 setup();lock_off=true;run();assert(!calls);
 setup();lock_edge=true;run();assert(!calls && p.esd_work.due==1000);
 setup();lock_deadlocks=1;reset_deadlocks=2;run();
 assert(backoffs==3 && calls==3 && resets==1 && p.esd_count==1 && done==1);
 setup();reset_error=-EIO;run();assert(calls==1 && !resets && p.esd_count==1 && done==1);
 setup();for(int i=0;i<5;i++){jiffies=i*1000;run();}assert(resets==5);
 jiffies=5000;run();assert(resets==5 && gives==1 && !p.esd_work.queued);
 jiffies=64000;run();assert(resets==5 && gives==1);
 jiffies=65000;run();assert(resets==6 && p.esd_count==1);
 /* Sliding window: five near its end must not allow five just past it. */
 setup();jiffies=0;assert(nt36523_esd_budget(&p));
 for(int i=0;i<4;i++){jiffies=59000+i;assert(nt36523_esd_budget(&p));}
 jiffies=60000;assert(nt36523_esd_budget(&p));
 jiffies=60001;assert(!nt36523_esd_budget(&p) && gives==1);
 setup();jiffies=~0UL-500;nt36523_esd_queue(&p);jiffies+=1000;run();assert(resets==1);
 for(int fail=1;fail<=2;fail++){
  setup();p.esd_ready=false;irq_fail=fail;nt36523_esd_init(&p);
  assert(!p.esd_ready && !p.esd_gpios && warnings==1 && freed==fail-1 && gpio_puts==1 && !p.esd_work.queued);
 }
 setup();p.esd_ready=false;pins[1].irq=-ENXIO;nt36523_esd_init(&p);
 assert(!p.esd_ready && warnings==1 && freed==1 && gpio_puts==1);
 setup();p.esd_ready=false;gpios.ndescs=1;nt36523_esd_init(&p);
 assert(!p.esd_ready && warnings==1 && !requests && gpio_puts==1);
 setup();p.esd_ready=false;gpio_fail=-EBUSY;nt36523_esd_init(&p);
 assert(!p.esd_ready && warnings==1 && !requests && !gpio_puts);
 setup();p.esd_ready=false;nt36523_esd_init(&p);
 assert(p.esd_ready && requests==2 && monitoring==1 && !warnings && p.esd_work.due==1000);
 puts("PASS: ESD debounce, disabled/off/error guards, DRM backoff/lifetime, rolling limit, IRQ failure cleanup");
 return 0;
}
'''
            (work / 'esd.c').write_text(harness)
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-Wno-unused-parameter',
                            str(work / 'esd.c'), '-o', str(work / 'esd')], check=True)
            subprocess.run([str(work / 'esd')], check=True)
            for callback in ('enable', 'disable', 'prepare', 'unprepare'):
                body = re.search(r'static int nt36523_' + callback +
                                 r'\(.*?\n}', source, re.S).group()
                self.assertNotIn('cancel_delayed_work_sync', body)
                self.assertNotIn('flush', body)

    def test_refresh_modes_and_packets(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            source = replay(work)
            def function(name, text=source):
                return re.search(r'(?:static )?(?:int|u8|unsigned int) ' + name +
                                 r'\(.*?\n}', text, re.S).group()
            upstream_modes = (UPSTREAM / 'drivers/gpu/drm/drm_modes.c').read_text()
            modes = re.search(r'static const struct drm_display_mode dby_w09_modes\[\] = .*?\n};',
                              source, re.S).group()
            desc = re.search(r'static const struct panel_desc dby_w09_desc = .*?\n};',
                             source, re.S).group()
            self.assertIn('.modes = dby_w09_modes,', desc)
            self.assertIn('.num_modes = ARRAY_SIZE(dby_w09_modes),', desc)
            harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>
#include <sys/types.h>
typedef uint8_t u8;
typedef uint16_t u16;
#define ARRAY_SIZE(a) (sizeof(a)/sizeof((a)[0]))
#define DRM_MODE_FLAG_INTERLACE 1
#define DRM_MODE_FLAG_DBLSCAN 2
#define DRM_MODE_TYPE_DRIVER 1
#define DRM_MODE_TYPE_PREFERRED 2
#define MIPI_DSI_MSG_USE_LPM 2
#define MIPI_DSI_DCS_SHORT_WRITE 5
#define MIPI_DSI_DCS_LONG_WRITE 0x39
#define MIPI_DCS_EXIT_SLEEP_MODE 0x11
#define check_mul_overflow(a,b,p) __builtin_mul_overflow(a,b,p)
#define mul_u32_u32(a,b) ((uint64_t)(a)*(b))
#define DIV_ROUND_CLOSEST_ULL(n,d) (((n)+(d)/2)/(d))
struct drm_display_mode {
 int clock,hdisplay,hsync_start,hsync_end,htotal,vdisplay,vsync_start,vsync_end,vtotal;
 unsigned int flags,vscan,type;
};
struct drm_crtc_state { struct drm_display_mode adjusted_mode; };
struct drm_crtc { struct drm_crtc_state *state; };
struct drm_connector_state { struct drm_crtc *crtc; };
struct drm_connector {
 struct drm_connector_state *state; void *dev;
 struct { int width_mm,height_mm,bpc; } display_info;
};
struct drm_panel { void *dev; };
struct mipi_dsi_msg { int channel,type,flags;size_t tx_len;const void *tx_buf; };
struct mipi_dsi_host;
struct host_ops { ssize_t (*transfer)(struct mipi_dsi_host *,const struct mipi_dsi_msg *); };
struct mipi_dsi_host { const struct host_ops *ops;int id; };
struct mipi_dsi_device { struct mipi_dsi_host *host;int channel; };
struct panel_desc { const struct drm_display_mode *modes;int num_modes,width_mm,height_mm,bpc; };
struct panel_info {
 struct drm_panel panel;struct drm_connector *connector;bool mode_fallback_warned;
 struct mipi_dsi_device *dsi[2];const struct panel_desc *desc;
};
struct kernel_param { void *arg; };
static int refresh_hz=120, non_burst;
static bool dby_params_locked;
static int warnings, logged_hz, logged_value, logs;
#define dev_warn(...) (++warnings)
#define dev_err(...) ((void)0)
#define dev_info(d,fmt,hz,value) do {logged_hz=hz;logged_value=value;logs++;} while (0)
static int kstrtoint(const char *s,int base,int *v) {
 char *end;long n=strtol(s,&end,base);if(*end || end==s)return -EINVAL;*v=n;return 0;
}
static struct panel_info *to_panel_info(struct drm_panel *p) {return (struct panel_info *)p;}
static struct drm_display_mode copies[3];
static int duplicated,probed,fail_duplicate;
static struct drm_display_mode *drm_mode_duplicate(void *d,const struct drm_display_mode *m) {
 (void)d;if(fail_duplicate)return NULL;assert(duplicated<3);copies[duplicated]=*m;return &copies[duplicated++];
}
static void drm_mode_set_name(struct drm_display_mode *m) {(void)m;}
static void drm_mode_probed_add(struct drm_connector *c,struct drm_display_mode *m) {(void)c;(void)m;probed++;}
struct dby_w09_cmd {u8 type,delay_ms,len,data[6];};
/* Synthetic commands only: no accepted private panel table in this test. */
static const struct dby_w09_cmd dby_w09_on[] = {
 {0x39,0,2,{0xff,0x2a}}, {0x15,0,2,{0x23,0x0c}}, {0x39,0,2,{0xff,0x10}},
 {5,7,1,{0x11}}, {5,9,1,{0x29}}, {0x15,0,2,{0x55,0x42}},
};
static const struct dby_w09_cmd dby_w09_off[] = {{5,2,1,{0x28}}, {5,3,1,{0x10}}};
struct packet {int link,type,flags;size_t len;u8 data[6];};
static struct packet packets[32];
static int n_packets,fail_packet,delay;
static ssize_t transfer(struct mipi_dsi_host *h,const struct mipi_dsi_msg *m) {
 int n=n_packets++;assert(n<32 && m->tx_len<=6);packets[n]=(struct packet){h->id,m->type,m->flags,m->tx_len,{0}};
 memcpy(packets[n].data,m->tx_buf,m->tx_len);
 return n==fail_packet ? -EIO : (ssize_t)m->tx_len;
}
static void msleep(int ms) {delay+=ms;}
'''
            harness += function('drm_mode_vrefresh', upstream_modes) + '\n' + modes
            harness += '\nstatic const struct panel_desc dby_w09_desc = {dby_w09_modes,3,145,232,8};\n'
            for name in ('dby_profile_set', 'dby_w09_send', 'dby_w09_current_refresh',
                         'dby_w09_refresh_value', 'dby_w09_set_refresh',
                         'dby_w09_init_sequence', 'dby_w09_off_sequence', 'nt36523_get_modes'):
                harness += function(name) + '\n'
            harness += r'''
int main(void) {
 const int rates[]={30,60,120}, vfp[]={8507,2853,26}, vt[]={11308,5654,2827}, values[]={14,12,13};
 struct drm_crtc_state crtc_state;struct drm_crtc crtc={&crtc_state};
 struct drm_connector_state state={&crtc};struct drm_connector con={.state=&state};
 const struct host_ops ops={transfer};struct mipi_dsi_host hosts[]={{&ops,0},{&ops,1}};
 struct mipi_dsi_device dsi[]={{&hosts[0],0},{&hosts[1],0}};
 struct panel_info p={.dsi={&dsi[0],&dsi[1]},.desc=&dby_w09_desc};
 struct kernel_param pref={&refresh_hz}, burst={&non_burst};
 assert(dby_profile_set("90",&pref)==-EINVAL && dby_profile_set("0",&pref)==-EINVAL);
 assert(dby_profile_set("30",&pref)==0 && dby_profile_set("60",&pref)==0 && dby_profile_set("120",&pref)==0);
 assert(dby_profile_set("1",&burst)==0 && non_burst==1 && dby_profile_set("2",&burst)==-EINVAL);
 dby_params_locked=true;assert(dby_profile_set("60",&pref)==-EBUSY);
 assert(dby_profile_set("120",&pref)==0 && dby_profile_set("0",&burst)==-EBUSY);
 for(int i=0;i<3;i++) {
  const struct drm_display_mode *m=&dby_w09_modes[i];
  assert(drm_mode_vrefresh(m)==rates[i] && m->clock==584849 && m->htotal==1724);
  assert(m->vsync_start-m->vdisplay==vfp[i] && m->vtotal==vt[i]);
  assert(m->hsync_start==1644 && m->hsync_end==1684 && m->vdisplay==2560);
  assert(m->vsync_end-m->vsync_start==4 && m->vtotal-m->vsync_end==237);
  assert(dby_w09_refresh_value(rates[i])==values[i]);
 }
 for(int preferred=0;preferred<3;preferred++) {
  refresh_hz=rates[preferred];duplicated=probed=0;
  assert(nt36523_get_modes(&p.panel,&con)==3 && duplicated==3 && probed==3);
  assert(p.connector==&con && con.display_info.width_mm==145 && con.display_info.height_mm==232 && con.display_info.bpc==8);
  for(int i=0;i<3;i++)assert(copies[i].type==(DRM_MODE_TYPE_DRIVER|(i==preferred?DRM_MODE_TYPE_PREFERRED:0)));
  for(int selected=0;selected<3;selected++) {
   crtc_state.adjusted_mode=dby_w09_modes[selected];n_packets=delay=logs=warnings=0;fail_packet=-1;
   assert(dby_w09_current_refresh(&p)==(unsigned)rates[selected]);
   assert(dby_w09_init_sequence(&p)==0 && logs==1 && logged_hz==rates[selected] && logged_value==values[selected]);
   assert(n_packets==20 && delay==16 && !warnings);
   for(int i=0;i<10;i++)for(int link=0;link<2;link++) {
    struct packet *q=&packets[2*i+link];assert(q->link==link);
    if(i>=3 && i<7) {
     const u8 expected[][2]={{0xff,0x2a},{0xfb,1},{0x23,values[selected]},{0xff,0x10}};
     assert(q->type==0x39 && q->flags==MIPI_DSI_MSG_USE_LPM && q->len==2 && !memcmp(q->data,expected[i-3],2));
    } else {
     const struct dby_w09_cmd *original=&dby_w09_on[i<3?i:i-4];
     assert(q->type==original->type && q->flags==MIPI_DSI_MSG_USE_LPM && q->len==original->len && !memcmp(q->data,original->data,q->len));
    }
   }
  }
 }
 /* Missing or unusable current state falls back once per panel, not per prepare. */
 for(int preferred=0;preferred<3;preferred++) {
  refresh_hz=rates[preferred];p.mode_fallback_warned=false;warnings=0;p.connector=NULL;
  assert(dby_w09_current_refresh(&p)==(unsigned)refresh_hz && warnings==1);
  p.connector=&con;con.state=NULL;assert(dby_w09_current_refresh(&p)==(unsigned)refresh_hz && warnings==1);
  con.state=&state;state.crtc=NULL;assert(dby_w09_current_refresh(&p)==(unsigned)refresh_hz && warnings==1);
  state.crtc=&crtc;crtc.state=NULL;assert(dby_w09_current_refresh(&p)==(unsigned)refresh_hz && warnings==1);
  crtc.state=&crtc_state;crtc_state.adjusted_mode=dby_w09_modes[1];crtc_state.adjusted_mode.clock=0;
  assert(dby_w09_current_refresh(&p)==(unsigned)refresh_hz && warnings==1);
 }
 crtc_state.adjusted_mode=dby_w09_modes[1];
 /* A failure on either link at any packet aborts before the next write. */
 for(int i=0;i<20;i++){n_packets=delay=0;fail_packet=i;assert(dby_w09_init_sequence(&p)==-EIO && n_packets==i+1);}
 n_packets=delay=0;fail_packet=-1;assert(dby_w09_off_sequence(&p)==0 && n_packets==4 && delay==5);
 for(int i=0;i<4;i++)assert(packets[i].flags==MIPI_DSI_MSG_USE_LPM && packets[i].data[0]==dby_w09_off[i/2].data[0]);
 hosts[0].ops=NULL;assert(dby_w09_init_sequence(&p)==-EOPNOTSUPP);hosts[0].ops=&ops;
 struct panel_desc other={dby_w09_modes,3,1,2,8};p.desc=&other;refresh_hz=120;duplicated=probed=0;
 assert(nt36523_get_modes(&p.panel,&con)==3);assert(copies[0].type==3 && copies[1].type==1 && copies[2].type==1);
 fail_duplicate=1;assert(nt36523_get_modes(&p.panel,&con)==-ENOMEM);
 puts("PASS: upstream vrefresh, preferred flags, active-mode override/fallback, LP dual-link writes, original LP sequence and failure aborts");
 return 0;
}
'''
            (work / 'refresh.c').write_text(harness)
            subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                            '-Wno-sign-compare', str(work / 'refresh.c'),
                            '-o', str(work / 'refresh')], check=True)
            subprocess.run([str(work / 'refresh')], check=True)

    def test_actual_functions(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            before_dir = work / 'before'
            after_dir = work / 'after'
            before_src = replay(before_dir, ('0001', '0002', '0003', '0011', '0013', '0014'))
            source = replay(after_dir)
            self.assertEqual(
                re.sub(r'static int nt36523_power_on\(struct panel_info \*pinfo\)\n\{.*?\n\}',
                       '<power_on>', before_src, count=1, flags=re.S),
                re.sub(r'static int nt36523_power_on\(struct panel_info \*pinfo\)\n\{.*?\n\}',
                       '<power_on>', source, count=1, flags=re.S),
            )
            names = ['nt36523_full_power', 'nt36523_power_off', 'nt36523_power_on',
                     'nt36523_prepare_power', 'nt36523_prepare', 'nt36523_unprepare']
            functions = '\n'.join(re.search(r'static (?:int|bool) ' + name +
                                  r'\(.*?\n}', source, re.S).group() for name in names)
            harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#define BIT(i) (1UL << (i))
#define ARRAY_SIZE(a) ((int)(sizeof(a)/sizeof((a)[0])))
#define dev_err(...) ((void)0)
struct regulator { int id, refs; };
struct drm_panel { void *dev; };
struct panel_info;
struct panel_desc { int (*init_sequence)(struct panel_info *); };
struct panel_info {
 struct drm_panel panel;
 struct regulator *vci, *vddio, *vsp, *vsn;
 unsigned long power_enabled;
 bool boot_power_cycled;
 void *reset_gpio;
 struct panel_desc *desc;
};
static int events[1024], n, fail_enable=-1, fail_disable=-1, fail_init;
static void emit(int x) { assert(n < 1024); events[n++]=x; }
static void msleep(int ms) { emit(1000+ms); }
static int regulator_enable(struct regulator *r) {
 emit(100+r->id); if(r->id == fail_enable) return -EIO;
 assert(r->refs == 0); r->refs++; return 0;
}
static int regulator_disable(struct regulator *r) {
 emit(200+r->id); assert(r->refs == 1);
 if(r->id == fail_disable) return -EIO;
 r->refs--; return 0;
}
static void gpiod_set_value_cansleep(void *p, int x) { (void)p; assert(x==1); emit(300); }
static struct panel_info *to_panel_info(struct drm_panel *p) { return (struct panel_info *)p; }
static void nt36523_reset(struct panel_info *p) { (void)p; emit(400); }
static int init(struct panel_info *p) { (void)p; emit(500); return fail_init ? -EIO : 0; }
'''
            harness += functions + r'''
static struct regulator rails[4];
static struct panel_desc desc = { init };
static struct panel_info setup(unsigned mask) {
 for(int i=0;i<4;i++) rails[i]=(struct regulator){i,0};
 n=0; fail_enable=fail_disable=-1; fail_init=0;
 return (struct panel_info){ .vci=mask&1?&rails[0]:NULL, .vddio=&rails[1],
 .vsp=mask&2?&rails[2]:NULL, .vsn=mask&4?&rails[3]:NULL, .desc=&desc };
}
static void empty(void) { for(int i=0;i<4;i++) assert(rails[i].refs==0); }
int main(void) {
 struct panel_info p=setup(0);
 assert(nt36523_prepare(&p.panel)==0); assert(nt36523_unprepare(&p.panel)==0);
 int legacy[]={101,400,500,300,201};
 assert(n==ARRAY_SIZE(legacy) && !memcmp(events,legacy,sizeof(legacy))); empty();
 p=setup(0);fail_enable=1;assert(nt36523_prepare(&p.panel)==-EIO);assert(n==1);empty();
 p=setup(0);fail_init=1;assert(nt36523_prepare(&p.panel)==-EIO);
 int legacy_fail[]={101,400,500,201};
 assert(n==ARRAY_SIZE(legacy_fail) && !memcmp(events,legacy_fail,sizeof(legacy_fail)));empty();
 p=setup(7);assert(nt36523_prepare(&p.panel)==0);
 int full[]={100,1001,101,1002,102,1002,103,1012,300,1005,203,1005,202,1010,201,200,1001,1100,
             100,1001,101,1002,102,1002,103,1012,400,500};
 assert(n==ARRAY_SIZE(full) && !memcmp(events,full,sizeof(full)));
 assert(nt36523_unprepare(&p.panel)==0);empty();n=0;
 assert(nt36523_prepare(&p.panel)==0);
 int repeat[]={100,1001,101,1002,102,1002,103,1012,400,500};
 assert(n==ARRAY_SIZE(repeat) && !memcmp(events,repeat,sizeof(repeat)));
 assert(nt36523_unprepare(&p.panel)==0);empty();
 for(unsigned mask=1;mask<8;mask++) {
  p=setup(mask);assert(nt36523_prepare(&p.panel)==0);assert(p.boot_power_cycled);
  assert(n>=4 && events[n-2]==400 && events[n-1]==500);
  if(mask & 4) assert(events[n-4]==103 && events[n-3]==1012);
  else if(mask & 2) assert(events[n-4]==102 && events[n-3]==1002);
  else assert(events[n-4]==101 && events[n-3]==1002);
  assert(nt36523_unprepare(&p.panel)==0);empty();
  for(int rail=0;rail<4;rail++) {
   p=setup(mask);struct regulator *present[]={p.vci,p.vddio,p.vsp,p.vsn};
   if(!present[rail]) continue;
   fail_enable=rail;assert(nt36523_prepare(&p.panel)==-EIO);empty();assert(!p.boot_power_cycled);
   fail_enable=-1;assert(nt36523_prepare(&p.panel)==0);assert(nt36523_unprepare(&p.panel)==0);empty();
   p=setup(mask);fail_disable=rail;assert(nt36523_prepare(&p.panel)==-EIO);
   assert(!p.boot_power_cycled && rails[rail].refs==1);
   fail_disable=-1;assert(nt36523_prepare(&p.panel)==0);assert(nt36523_unprepare(&p.panel)==0);empty();
   p=setup(mask);assert(nt36523_prepare(&p.panel)==0);fail_disable=rail;
   assert(nt36523_unprepare(&p.panel)==-EIO);assert(rails[rail].refs==1);
   fail_disable=-1;assert(nt36523_prepare(&p.panel)==0);assert(nt36523_unprepare(&p.panel)==0);empty();
  }
  p=setup(mask);fail_init=1;assert(nt36523_prepare(&p.panel)==-EIO);empty();
 }
 puts("PASS: legacy traces, 7 supply combinations, all enable/disable failures and retries");
}
'''
            (work / 'test.c').write_text(harness)
            subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Wno-unused-variable',
                            '-Werror', str(work / 'test.c'), '-o', str(work / 'test')], check=True)
            subprocess.run([str(work / 'test')], check=True)


if __name__ == '__main__':
    unittest.main()
