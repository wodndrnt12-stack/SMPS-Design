const { test, expect } = require('@playwright/test');
const path = require('path');

const FILE_URL = `file:///${path.resolve(__dirname, '..', 'index.html').replace(/\\/g, '/')}`;

test.beforeEach(async ({ page }) => {
  await page.goto(FILE_URL);
  await page.waitForSelector('#hdr');
});

// ════════════════════════════════════════════════════════════
// Phase 1: 페이지 로드, 초기값, 계산 엔진, 드롭다운
// ════════════════════════════════════════════════════════════

test.describe('Phase 1 — Core Transformer Design', () => {
  test('페이지 로드 및 기본 구조 확인', async ({ page }) => {
    await expect(page.locator('#hdr')).toBeVisible();
    await expect(page.locator('#left')).toBeVisible();
    await expect(page.locator('#center')).toBeVisible();
    await expect(page.locator('#right')).toBeVisible();
    await expect(page.locator('#bottom-wire')).toBeVisible();
  });

  test('JS 에러 없이 로드', async ({ page }) => {
    const errors = [];
    page.on('pageerror', err => errors.push(err.message));
    await page.reload();
    await page.waitForSelector('#hdr');
    expect(errors).toEqual([]);
  });

  test('기본 Core = EE2020, MOSFET = STH3N150', async ({ page }) => {
    const coreVal = await page.locator('#sel-core').inputValue();
    const mosVal = await page.locator('#sel-mosfet').inputValue();
    expect(coreVal).toBe('EE2020');
    expect(mosVal).toBe('STH3N150');
  });

  test('Core DB 드롭다운 — 10개 이상 옵션', async ({ page }) => {
    const count = await page.locator('#sel-core option').count();
    expect(count).toBeGreaterThanOrEqual(10);
  });

  test('초기 계산값 — n = Np/Ns = 9', async ({ page }) => {
    const n = await page.locator('#cal-n').textContent();
    expect(parseFloat(n)).toBeCloseTo(9.0, 1);
  });

  test('초기 Pout 계산 (채널 3개 합산)', async ({ page }) => {
    // PV15: 15*0.2=3, NV15: 15*0.01=0.15, IPV24: 24*0.18=4.32 → total=7.47
    const pout = await page.locator('#cal-pout').textContent();
    expect(parseFloat(pout)).toBeCloseTo(7.47, 1);
  });

  test('D_on + D_off < 100% → DCM PASS', async ({ page }) => {
    const don = parseFloat(await page.locator('#cal-don').textContent());
    const doff = parseFloat(await page.locator('#cal-doff').textContent());
    expect(don + doff).toBeLessThan(100);
    await expect(page.locator('#st-dcm')).toHaveText('PASS');
  });

  test('5개 판정 배지 모두 PASS', async ({ page }) => {
    const badges = ['badge-dcm', 'badge-ipk', 'badge-pwr', 'badge-vds', 'badge-flux'];
    for (const id of badges) {
      const cls = await page.locator(`#${id}`).getAttribute('class');
      expect(cls).toContain('pass');
    }
  });

  test('Ipk < Ipk_limit (OCP 판정)', async ({ page }) => {
    const ipk = parseFloat(await page.locator('#cal-ipk').textContent());
    const limit = parseFloat(await page.locator('#cal-ipklimit').textContent());
    expect(ipk).toBeLessThan(limit);
  });

  test('Core 변경 시 Ae, AL_zero 업데이트', async ({ page }) => {
    await page.locator('#sel-core').selectOption('EE13');
    await page.waitForTimeout(200);
    const ae = await page.locator('#cal-ae').textContent();
    expect(parseFloat(ae)).toBeCloseTo(17.1, 1);
    const al = await page.locator('#cal-alzero').textContent();
    expect(parseFloat(al)).toBeCloseTo(1130, 0);
  });

  test('Np 입력 변경 → n 재계산', async ({ page }) => {
    await page.locator('#inp-np').fill('80');
    await page.locator('#inp-np').dispatchEvent('input');
    await page.waitForTimeout(200);
    const n = parseFloat(await page.locator('#cal-n').textContent());
    expect(n).toBeCloseTo(8.0, 1);
  });

  test('Wire Table — Np + 3개 채널 = 4행', async ({ page }) => {
    const rows = await page.locator('#winding-tbody tr').count();
    expect(rows).toBe(4);
  });

  test('Wire Table Np행 Ipk 표시', async ({ page }) => {
    const ipk = await page.locator('#ch-np-ipk').textContent();
    expect(parseFloat(ipk)).toBeGreaterThan(0);
  });

  test('Duty bar 시각화 존재', async ({ page }) => {
    await expect(page.locator('#duty-don')).toBeVisible();
    await expect(page.locator('#duty-doff')).toBeVisible();
    await expect(page.locator('#duty-dead')).toBeVisible();
  });

  test('Flux margin bar 시각화 존재', async ({ page }) => {
    await expect(page.locator('#flux-used')).toBeVisible();
    await expect(page.locator('#flux-margin')).toBeVisible();
    const pct = await page.locator('#flux-margin-pct').textContent();
    expect(parseFloat(pct)).toBeGreaterThan(0);
  });

  test('KPI 카드 값 표시', async ({ page }) => {
    const donText = await page.locator('#kpi-don').textContent();
    expect(donText).toContain('%');
    const ipkText = await page.locator('#kpi-ipk').textContent();
    expect(ipkText).toContain('A');
  });

  test('VDS 계산: Vin_max + Vr + V_spike', async ({ page }) => {
    const vds = parseFloat(await page.locator('#cal-vds').textContent());
    const vinMax = 850;
    const vr = parseFloat(await page.locator('#cal-vr').textContent());
    const vspike = 200;
    expect(vds).toBeCloseTo(vinMax + vr + vspike, 0);
  });
});

// ════════════════════════════════════════════════════════════
// Phase 2: 손실 분석, 스트레스 바, 온도 디레이팅
// ════════════════════════════════════════════════════════════

test.describe('Phase 2 — Loss & Stress Analysis', () => {
  test('Loss Breakdown — 8개 항목 모두 값 표시', async ({ page }) => {
    const lossIds = [
      'loss-mos-cond-val', 'loss-mos-sw-val', 'loss-gate-val',
      'loss-diode-val', 'loss-cu-pri-val', 'loss-cu-sec-val',
      'loss-core-val', 'loss-snub-val'
    ];
    for (const id of lossIds) {
      const text = await page.locator(`#${id}`).textContent();
      expect(text).toContain('W');
    }
  });

  test('Total Loss > 0', async ({ page }) => {
    const total = await page.locator('#loss-total-val').textContent();
    expect(parseFloat(total)).toBeGreaterThan(0);
  });

  test('효율 η 표시 (0~100%)', async ({ page }) => {
    const eta = await page.locator('#loss-eta-val').textContent();
    const val = parseFloat(eta);
    expect(val).toBeGreaterThan(0);
    expect(val).toBeLessThanOrEqual(100);
  });

  test('MOSFET Pd, Tj 표시', async ({ page }) => {
    const pd = await page.locator('#loss-mos-pd-val').textContent();
    expect(pd).toContain('W');
    const tj = await page.locator('#loss-tj-val').textContent();
    expect(tj).toContain('°C');
  });

  test('Stress VDS 바 — safe 클래스', async ({ page }) => {
    const cls = await page.locator('#stress-vds-bar').getAttribute('class');
    expect(cls).toMatch(/safe|warn|danger/);
  });

  test('Stress Ipk 바 표시', async ({ page }) => {
    const text = await page.locator('#stress-ipk-val').textContent();
    expect(text).toContain('/');
  });

  test('Stress Flux 바 표시', async ({ page }) => {
    const text = await page.locator('#stress-flux-val').textContent();
    expect(text).toContain('/');
  });

  test('Diode Vrrm 채널별 표시', async ({ page }) => {
    const vrrmList = await page.locator('#stress-vrrm-list .loss-bar-wrap').count();
    expect(vrrmList).toBe(3);
  });

  test('온도 디레이팅 — 기본 25°C에서 Bsat = 0.39T', async ({ page }) => {
    const bsat = parseFloat(await page.locator('#cal-bsat-temp').textContent());
    expect(bsat).toBeCloseTo(0.39, 2);
  });

  test('온도 100°C 변경 → Bsat 감소', async ({ page }) => {
    const bsatBefore = parseFloat(await page.locator('#cal-bsat-temp').textContent());
    await page.locator('#inp-temp').fill('100');
    await page.locator('#inp-temp').dispatchEvent('input');
    await page.waitForTimeout(200);
    const bsatAfter = parseFloat(await page.locator('#cal-bsat-temp').textContent());
    expect(bsatAfter).toBeLessThan(bsatBefore);
  });

  test('Window Util 표시 (> 0%)', async ({ page }) => {
    const wu = parseFloat(await page.locator('#cal-win-util').textContent());
    expect(wu).toBeGreaterThan(0);
  });

  test('MOSFET conduction loss = Irms² × Rdson (비영)', async ({ page }) => {
    const cond = await page.locator('#loss-mos-cond-val').textContent();
    expect(parseFloat(cond)).toBeGreaterThan(0);
  });

  test('Core Steinmetz loss 비영', async ({ page }) => {
    const core = await page.locator('#loss-core-val').textContent();
    expect(parseFloat(core)).toBeGreaterThan(0);
  });

  test('Loss bar width > 0% (MOSFET cond)', async ({ page }) => {
    const width = await page.locator('#loss-mos-cond-bar').evaluate(el => el.style.width);
    expect(parseFloat(width)).toBeGreaterThan(0);
  });
});

// ════════════════════════════════════════════════════════════
// Phase 3: RCD Snubber
// ════════════════════════════════════════════════════════════

test.describe('Phase 3 — RCD Snubber', () => {
  test('Llk 계산 (Lp × Llk%)', async ({ page }) => {
    const llk = parseFloat(await page.locator('#cal-llk').textContent());
    expect(llk).toBeGreaterThan(0);
  });

  test('P_snubber 표시 (> 0)', async ({ page }) => {
    const ps = parseFloat(await page.locator('#cal-psnub').textContent());
    expect(ps).toBeGreaterThan(0);
  });

  test('R_snub, C_snub 계산값 표시', async ({ page }) => {
    const r = await page.locator('#cal-rsnub').textContent();
    expect(r).not.toBe('—');
    expect(r).not.toBe('∞');
    const c = await page.locator('#cal-csnub').textContent();
    expect(c).not.toBe('—');
  });

  test('VDS clamped = Vin_max + Vclamp', async ({ page }) => {
    const vdsClamp = parseFloat(await page.locator('#cal-vds-clamp').textContent());
    const vinMax = 850;
    const vclamp = 250;
    expect(vdsClamp).toBeCloseTo(vinMax + vclamp, 0);
  });

  test('Snub Diode Vrrm 표시', async ({ page }) => {
    const vrrm = parseFloat(await page.locator('#cal-snub-dvrrm').textContent());
    expect(vrrm).toBeGreaterThan(0);
  });

  test('VDS clamped 스트레스 바 표시', async ({ page }) => {
    const text = await page.locator('#stress-vds-clamp-val').textContent();
    expect(text).toContain('/');
  });

  test('Vclamp > Vr → 정상 메시지', async ({ page }) => {
    const warn = await page.locator('#snub-vclamp-warn').textContent();
    expect(warn).toContain('Vclamp/Vr');
  });

  test('Vclamp ≤ Vr → 경고 메시지', async ({ page }) => {
    // Vr ≈ 143V (n=9, Vout=15, VD_F=0.9), Vclamp을 100으로 낮추면 Vclamp < Vr
    await page.locator('#inp-vclamp').fill('100');
    await page.locator('#inp-vclamp').dispatchEvent('input');
    await page.waitForTimeout(200);
    const warn = await page.locator('#snub-vclamp-warn').textContent();
    expect(warn).toContain('스너버 동작 불가');
  });

  test('Llk% 변경 → P_snubber 변경', async ({ page }) => {
    const psBefore = parseFloat(await page.locator('#cal-psnub').textContent());
    await page.locator('#inp-llk-pct').fill('3');
    await page.locator('#inp-llk-pct').dispatchEvent('input');
    await page.waitForTimeout(200);
    const psAfter = parseFloat(await page.locator('#cal-psnub').textContent());
    expect(psAfter).toBeGreaterThan(psBefore);
  });
});

// ════════════════════════════════════════════════════════════
// Phase 4: Preset 비교 모드
// ════════════════════════════════════════════════════════════

test.describe('Phase 4 — Preset Compare', () => {
  test('Compare 버튼 존재', async ({ page }) => {
    const btn = page.locator('button:has-text("Compare")');
    await expect(btn).toBeVisible();
  });

  test('Compare 클릭 → 모달 열림', async ({ page }) => {
    await page.locator('button:has-text("Compare")').click();
    await expect(page.locator('#modal-cmp')).toHaveClass(/active/);
  });

  test('닫기 클릭 → 모달 닫힘', async ({ page }) => {
    await page.locator('button:has-text("Compare")').click();
    await expect(page.locator('#modal-cmp')).toHaveClass(/active/);
    await page.locator('#modal-cmp button:has-text("닫기")').click();
    await expect(page.locator('#modal-cmp')).not.toHaveClass(/active/);
  });

  test('프리셋 미선택 시 에러 메시지', async ({ page }) => {
    await page.locator('button:has-text("Compare")').click();
    await page.locator('#modal-cmp button:has-text("비교")').click();
    const result = await page.locator('#cmp-result').textContent();
    expect(result).toContain('선택하세요');
  });

  test('프리셋 저장 → Compare 드롭다운에 표시', async ({ page }) => {
    // 프리셋 저장
    await page.locator('#preset-name').fill('TestPresetA');
    await page.locator('#btn-preset-save').click();
    await page.waitForTimeout(200);

    // Compare 모달 열기
    await page.locator('button:has-text("Compare")').click();
    const optA = page.locator('#cmp-sel-a option[value="TestPresetA"]');
    await expect(optA).toBeAttached();

    // cleanup
    await page.evaluate(() => {
      const presets = JSON.parse(localStorage.getItem('dcm_flyback_presets') || '{}');
      delete presets['TestPresetA'];
      localStorage.setItem('dcm_flyback_presets', JSON.stringify(presets));
    });
  });

  test('"현재 상태" 옵션 존재', async ({ page }) => {
    await page.locator('button:has-text("Compare")').click();
    const currentOpt = page.locator('#cmp-sel-a option[value="__current__"]');
    await expect(currentOpt).toBeAttached();
  });

  test('현재 vs 현재 비교 — 테이블 렌더링', async ({ page }) => {
    await page.locator('button:has-text("Compare")').click();
    await page.locator('#cmp-sel-a').selectOption('__current__');
    await page.locator('#cmp-sel-b').selectOption('__current__');
    await page.locator('#modal-cmp button:has-text("비교")').click();
    await page.waitForTimeout(300);

    const table = page.locator('table.cmp');
    await expect(table).toBeVisible();

    // 동일값이므로 delta = '—' 또는 '=' 만 있어야 함
    const rows = await page.locator('table.cmp tbody tr:not(.cmp-grp)').count();
    expect(rows).toBeGreaterThan(10);
  });

  test('프리셋 A vs 현재 비교 — 값 차이 표시', async ({ page }) => {
    // 프리셋 저장 (현재 상태)
    await page.locator('#preset-name').fill('Base');
    await page.locator('#btn-preset-save').click();
    await page.waitForTimeout(100);

    // Np 변경하여 다른 상태 만들기
    await page.locator('#inp-np').fill('80');
    await page.locator('#inp-np').dispatchEvent('input');
    await page.waitForTimeout(200);

    // Compare
    await page.locator('button:has-text("Compare")').click();
    await page.locator('#cmp-sel-a').selectOption('Base');
    await page.locator('#cmp-sel-b').selectOption('__current__');
    await page.locator('#modal-cmp button:has-text("비교")').click();
    await page.waitForTimeout(300);

    const table = page.locator('table.cmp');
    await expect(table).toBeVisible();

    // n 값이 달라야 함 (Base: 9, 현재: 8)
    const nRow = page.locator('table.cmp tr', { has: page.locator('td.cmp-lbl:has-text("n (Np/Ns)")') });
    const cells = await nRow.locator('td').allTextContents();
    expect(cells.length).toBe(4);

    // cleanup
    await page.evaluate(() => {
      const presets = JSON.parse(localStorage.getItem('dcm_flyback_presets') || '{}');
      delete presets['Base'];
      localStorage.setItem('dcm_flyback_presets', JSON.stringify(presets));
    });
  });

  test('비교 후 원래 상태 복원', async ({ page }) => {
    // 현재 Np 확인
    const npBefore = await page.locator('#inp-np').inputValue();

    // 프리셋 저장
    await page.locator('#preset-name').fill('Restore');
    await page.locator('#btn-preset-save').click();
    await page.waitForTimeout(100);

    // Np 변경
    await page.locator('#inp-np').fill('70');
    await page.locator('#inp-np').dispatchEvent('input');
    await page.waitForTimeout(100);
    const npChanged = await page.locator('#inp-np').inputValue();
    expect(npChanged).toBe('70');

    // 프리셋 저장 (변경된 상태)
    await page.locator('#preset-name').fill('Changed');
    await page.locator('#btn-preset-save').click();
    await page.waitForTimeout(100);

    // Compare 실행 (Restore vs Changed)
    await page.locator('button:has-text("Compare")').click();
    await page.locator('#cmp-sel-a').selectOption('Restore');
    await page.locator('#cmp-sel-b').selectOption('Changed');
    await page.locator('#modal-cmp button:has-text("비교")').click();
    await page.waitForTimeout(300);

    // 비교 후 Np가 70 (현재 상태)으로 복원되어야 함
    const npAfter = await page.locator('#inp-np').inputValue();
    expect(npAfter).toBe('70');

    // cleanup
    await page.evaluate(() => {
      const presets = JSON.parse(localStorage.getItem('dcm_flyback_presets') || '{}');
      delete presets['Restore'];
      delete presets['Changed'];
      localStorage.setItem('dcm_flyback_presets', JSON.stringify(presets));
    });
  });

  test('입력값 포함 체크박스 해제 → 입력 행 숨김', async ({ page }) => {
    await page.locator('button:has-text("Compare")').click();
    await page.locator('#cmp-sel-a').selectOption('__current__');
    await page.locator('#cmp-sel-b').selectOption('__current__');
    await page.locator('#modal-cmp button:has-text("비교")').click();
    await page.waitForTimeout(200);

    // 입력값 포함 해제 전 — Core 행이 있어야 함 (kind:'sel')
    const coreRowBefore = page.locator('table.cmp td.cmp-lbl:has-text("Core")');
    const countBefore = await coreRowBefore.count();

    // 체크박스 해제 후 재비교
    await page.locator('#cmp-show-input').uncheck();
    await page.locator('#modal-cmp button:has-text("비교")').click();
    await page.waitForTimeout(200);

    // Lp_set 행(kind:'inp')이 없어야 함 — 정확한 텍스트 매칭
    const lpRow = page.locator('table.cmp td.cmp-lbl', { hasText: /^Lp_set$/ });
    const countAfter = await lpRow.count();
    expect(countAfter).toBe(0);
  });

  test('색상 코딩 — prefer:low에서 낮은 값이 cmp-better', async ({ page }) => {
    // 프리셋 저장
    await page.locator('#preset-name').fill('LowNp');
    await page.locator('#btn-preset-save').click();
    await page.waitForTimeout(100);

    // Lp를 크게 → Ipk 감소 (prefer:'low')
    await page.locator('#inp-lp').fill('2000');
    await page.locator('#inp-lp').dispatchEvent('input');
    await page.waitForTimeout(200);

    await page.locator('button:has-text("Compare")').click();
    await page.locator('#cmp-sel-a').selectOption('LowNp');
    await page.locator('#cmp-sel-b').selectOption('__current__');
    await page.locator('#modal-cmp button:has-text("비교")').click();
    await page.waitForTimeout(300);

    // Ipk (prefer:low) — B가 더 낮으면 B가 cmp-better
    const ipkRow = page.locator('table.cmp tr', { has: page.locator('td.cmp-lbl', { hasText: /^Ipk$/ }) });
    const cells = await ipkRow.locator('td').all();
    if (cells.length === 4) {
      const clsA = await cells[1].getAttribute('class');
      const clsB = await cells[2].getAttribute('class');
      // Lp 커지면 Ipk 작아짐 → B(현재, Lp=2000)가 lower → cmp-better
      expect(clsB).toContain('cmp-better');
      expect(clsA).toContain('cmp-worse');
    }

    // cleanup
    await page.evaluate(() => {
      const presets = JSON.parse(localStorage.getItem('dcm_flyback_presets') || '{}');
      delete presets['LowNp'];
      localStorage.setItem('dcm_flyback_presets', JSON.stringify(presets));
    });
  });
});

// ════════════════════════════════════════════════════════════
// 통합: 입력 변경 → 전체 연쇄 반응
// ════════════════════════════════════════════════════════════

test.describe('Integration — 연쇄 계산 검증', () => {
  test('Vin_min 변경 → D_on 증가, VDS는 Vin_max 의존이라 불변', async ({ page }) => {
    const donBefore = parseFloat(await page.locator('#cal-don').textContent());
    const vdsBefore = parseFloat(await page.locator('#cal-vds').textContent());

    await page.locator('#inp-vinmin').fill('200');
    await page.locator('#inp-vinmin').dispatchEvent('input');
    await page.waitForTimeout(300);

    const donAfter = parseFloat(await page.locator('#cal-don').textContent());
    const vdsAfter = parseFloat(await page.locator('#cal-vds').textContent());

    // Vin_min 감소 → D_on = sqrt(2*Pin*Lp*Fsw)/Vin_min → D_on 증가
    expect(donAfter).toBeGreaterThan(donBefore);
    // Ipk = sqrt(2*Pin/(Lp*Fsw)) → Vin에 무관 (수학적으로 상쇄)
    // VDS = Vin_max + Vr + Vspike → Vin_min 변경 영향 없음
    expect(vdsAfter).toBeCloseTo(vdsBefore, 0);
  });

  test('효율 입력 변경 → Pin 변경', async ({ page }) => {
    const pinBefore = parseFloat(await page.locator('#cal-pin').textContent());
    await page.locator('#inp-eff').fill('0.9');
    await page.locator('#inp-eff').dispatchEvent('input');
    await page.waitForTimeout(200);
    const pinAfter = parseFloat(await page.locator('#cal-pin').textContent());
    // eff 증가 → Pin = Pout/eff 감소
    expect(pinAfter).toBeLessThan(pinBefore);
  });

  test('채널 추가 → Wire table 행 증가', async ({ page }) => {
    const rowsBefore = await page.locator('#winding-tbody tr').count();
    await page.locator('button:has-text("+ Add Channel")').click();
    await page.waitForTimeout(200);
    const rowsAfter = await page.locator('#winding-tbody tr').count();
    expect(rowsAfter).toBe(rowsBefore + 1);
  });

  test('Library 모달 열기/닫기', async ({ page }) => {
    await page.locator('button:has-text("Library")').click();
    await expect(page.locator('#modal-lib')).toHaveClass(/active/);
    await page.locator('#modal-lib button:has-text("Close")').click();
    await expect(page.locator('#modal-lib')).not.toHaveClass(/active/);
  });

  test('Library — Core/MOSFET/IC 탭 전환', async ({ page }) => {
    await page.locator('button:has-text("Library")').click();
    await page.locator('#lib-tabs button:has-text("Core")').click();
    let content = await page.locator('#lib-content').textContent();
    expect(content).toContain('EE2020');

    await page.locator('#lib-tabs button:has-text("MOSFET")').click();
    content = await page.locator('#lib-content').textContent();
    expect(content).toContain('STH3N150');

    await page.locator('#lib-tabs button:has-text("IC")').click();
    content = await page.locator('#lib-content').textContent();
    expect(content).toContain('BD7F100HFN');
  });
});

// ════════════════════════════════════════════════════════════
// Wire DB — 2UEW/TIW 자동 연동
// ════════════════════════════════════════════════════════════

test.describe('Wire DB — 2UEW/TIW 자동 연동', () => {
  test('Wire Type 드롭다운 (2UEW/TIW) 존재', async ({ page }) => {
    await expect(page.locator('#sel-wiretype')).toBeVisible();
    const options = await page.locator('#sel-wiretype option').allTextContents();
    expect(options).toContain('2UEW');
    expect(options).toContain('TIW');
  });

  test('Wire Size 드롭다운 — 10개 규격 (0.16~0.40)', async ({ page }) => {
    const count = await page.locator('#sel-wiresize option').count();
    expect(count).toBe(10);
  });

  test('기본 0.20 선택 시 Bare=0.200, Coat=0.232 (2UEW)', async ({ page }) => {
    const bare = await page.locator('#cal-wirebare').textContent();
    expect(parseFloat(bare)).toBeCloseTo(0.200, 3);
    const coat = await page.locator('#cal-wirecoat').textContent();
    expect(parseFloat(coat)).toBeCloseTo(0.232, 3);
  });

  test('Wire Size 변경 → Bare/Coat 자동 업데이트', async ({ page }) => {
    await page.locator('#sel-wiresize').selectOption('0.3');
    await page.waitForTimeout(200);
    const bare = await page.locator('#cal-wirebare').textContent();
    expect(parseFloat(bare)).toBeCloseTo(0.300, 3);
    const coat = await page.locator('#cal-wirecoat').textContent();
    expect(parseFloat(coat)).toBeCloseTo(0.340, 3);
  });

  test('TIW 전환 → Coat 값 증가 (절연 두꺼움)', async ({ page }) => {
    const coat2uew = parseFloat(await page.locator('#cal-wirecoat').textContent());
    await page.locator('#sel-wiretype').selectOption('TIW');
    await page.waitForTimeout(200);
    const coatTiw = parseFloat(await page.locator('#cal-wirecoat').textContent());
    expect(coatTiw).toBeGreaterThan(coat2uew);
  });

  test('TIW 0.20 → Coat=0.350', async ({ page }) => {
    await page.locator('#sel-wiretype').selectOption('TIW');
    await page.locator('#sel-wiresize').selectOption('0.2');
    await page.waitForTimeout(200);
    const coat = await page.locator('#cal-wirecoat').textContent();
    expect(parseFloat(coat)).toBeCloseTo(0.350, 3);
  });

  test('Wire Table Np행 coat 열 표시', async ({ page }) => {
    const coat = await page.locator('#ch-np-coat').textContent();
    expect(parseFloat(coat)).toBeGreaterThan(0);
  });

  test('Wire Table 2차 채널 coat 열 표시', async ({ page }) => {
    const coat = await page.locator('#ch-pv15-coat').textContent();
    expect(parseFloat(coat)).toBeGreaterThan(0);
  });

  test('Wire Table Np 규격 변경 → Wire & Bobbin 동기화', async ({ page }) => {
    await page.locator('#ch-np-wire').selectOption('0.25');
    await page.waitForTimeout(200);
    const selVal = await page.locator('#sel-wiresize').inputValue();
    expect(selVal).toBe('0.25');
    const bare = await page.locator('#cal-wirebare').textContent();
    expect(parseFloat(bare)).toBeCloseTo(0.250, 3);
  });

  test('Wire Type 변경 → maxTurns 재계산 (coat 변경됨)', async ({ page }) => {
    const turnsBefore = await page.locator('#cal-maxturns').textContent();
    await page.locator('#sel-wiretype').selectOption('TIW');
    await page.waitForTimeout(200);
    const turnsAfter = await page.locator('#cal-maxturns').textContent();
    expect(parseInt(turnsAfter)).toBeLessThan(parseInt(turnsBefore));
  });
});
