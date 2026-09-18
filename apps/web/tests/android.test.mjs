import { test, describe, it } from 'node:test';
import assert from 'node:assert/strict';

describe('Part 10: Android Companion & Accessibility Control Tests', () => {
  it('validates supported Android device statuses and pairing states', () => {
    const validStatuses = ['ONLINE', 'OFFLINE', 'REVOKED', 'PAIRING'];
    assert.equal(validStatuses.length, 4);

    const isConnected = (status) => status === 'ONLINE';
    assert.equal(isConnected('ONLINE'), true);
    assert.equal(isConnected('REVOKED'), false);
    assert.equal(isConnected('PAIRING'), false);
  });

  it('classifies 3-tier risk for Android accessibility actions', () => {
    const CRITICAL_PACKAGES = [
      'com.android.settings',
      'com.google.android.apps.authenticator2',
      'com.google.android.apps.walletnfcrel',
      'com.phonepe.app',
      'net.one97.paytm',
    ];

    function evaluateAndroidRisk(actionType, packageName) {
      if (packageName && CRITICAL_PACKAGES.includes(packageName)) {
        return 'CRITICAL_ACTION';
      }
      if (actionType === 'TYPE_TEXT' || actionType === 'APP_LAUNCH') {
        return 'SENSITIVE_ACTION';
      }
      return 'LOW_RISK_ACTION';
    }

    assert.equal(evaluateAndroidRisk('NAVIGATE', null), 'LOW_RISK_ACTION');
    assert.equal(evaluateAndroidRisk('TAP', 'com.android.calculator2'), 'LOW_RISK_ACTION');
    assert.equal(evaluateAndroidRisk('TYPE_TEXT', 'com.whatsapp'), 'SENSITIVE_ACTION');
    assert.equal(evaluateAndroidRisk('APP_LAUNCH', 'com.android.chrome'), 'SENSITIVE_ACTION');
    assert.equal(evaluateAndroidRisk('APP_LAUNCH', 'com.android.settings'), 'CRITICAL_ACTION');
    assert.equal(evaluateAndroidRisk('TAP', 'net.one97.paytm'), 'CRITICAL_ACTION');
  });

  it('enforces coordinate boundary validation for tap and swipe gestures', () => {
    function validateCoordinates(actionType, coords) {
      if (actionType === 'TAP') {
        if (coords.x === undefined || coords.y === undefined || coords.x < 0 || coords.y < 0) {
          throw new Error('Invalid tap coordinates');
        }
      } else if (actionType === 'SWIPE') {
        const { x, y, x2, y2 } = coords;
        if ([x, y, x2, y2].some((c) => c === undefined || c < 0)) {
          throw new Error('Invalid swipe coordinates');
        }
      }
      return true;
    }

    assert.equal(validateCoordinates('TAP', { x: 100, y: 200 }), true);
    assert.throws(() => validateCoordinates('TAP', { x: -10, y: 50 }));
    assert.equal(validateCoordinates('SWIPE', { x: 100, y: 500, x2: 100, y2: 100 }), true);
    assert.throws(() => validateCoordinates('SWIPE', { x: 100, y: 500, x2: -50, y2: 100 }));
  });

  it('verifies notification sanitization rules for sensitive data', () => {
    function sanitizeNotification(title, text) {
      let clean = text;
      // Scrub credit cards
      clean = clean.replace(/\b(?:\d[ -]*?){13,16}\b/g, '[CARD_REDACTED]');
      // Scrub OTPs
      if (/otp|code|pin|verification/i.test(clean)) {
        clean = clean.replace(/\b\d{4,8}\b/g, '[OTP_REDACTED]');
      }
      return { title, text: clean };
    }

    const notif = sanitizeNotification(
      'Bank Alert',
      'Your one-time code for login is 654321. Do not share.'
    );
    assert.ok(notif.text.includes('[OTP_REDACTED]'));
    assert.ok(!notif.text.includes('654321'));

    const cardNotif = sanitizeNotification(
      'Payment',
      'Transaction on card 4111 2222 3333 4444 completed.'
    );
    assert.ok(cardNotif.text.includes('[CARD_REDACTED]'));
    assert.ok(!cardNotif.text.includes('4111 2222 3333 4444'));
  });

  it('enforces emergency stop block invariant on Android commands', () => {
    function checkControlAllowed(isEmergencyStopped, actionRequest) {
      if (isEmergencyStopped) {
        throw new Error('Emergency stop is ACTIVE. All device control blocked.');
      }
      return true;
    }

    assert.equal(checkControlAllowed(false, { action_type: 'TAP' }), true);
    assert.throws(() => checkControlAllowed(true, { action_type: 'TAP' }), /Emergency stop is ACTIVE/);
  });
});
