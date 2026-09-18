'use client';

import React, { useState, useEffect } from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import {
  Monitor,
  Smartphone,
  Plus,
  Trash2,
  AlertOctagon,
  ShieldCheck,
  ShieldAlert,
  Terminal,
  MousePointer,
  CheckCircle2,
  AlertTriangle,
  Loader2,
  Play,
  RotateCcw,
  Key,
  Battery,
  Wifi,
  Bell,
  Navigation,
  Send,
  Radio,
  ArrowRight,
} from 'lucide-react';
import { apiClient } from '@/lib/api';
import type {
  PairedComputer,
  ComputerScope,
  ComputerActionType,
  ComputerExecutionResult,
  ComputerStepProgress,
  AndroidDevice,
  AndroidContextPayload,
  AndroidActionRequest,
} from '@jenna/types';

export default function DevicesPage() {
  const [deviceTab, setDeviceTab] = useState<'pc' | 'android'>('pc');

  // PC State
  const [computers, setComputers] = useState<PairedComputer[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [isEmergencyStopped, setIsEmergencyStopped] = useState<boolean>(false);

  // PC Pairing Modal State
  const [showPairModal, setShowPairModal] = useState<boolean>(false);
  const [newDeviceName, setNewDeviceName] = useState<string>('');
  const [newDevicePlatform, setNewDevicePlatform] = useState<string>('linux');
  const [activePairingData, setActivePairingData] = useState<{
    device_id: string;
    pairing_code: string;
    expires_at: string;
  } | null>(null);
  const [inputPairingCode, setInputPairingCode] = useState<string>('');
  const [isPairing, setIsPairing] = useState<boolean>(false);

  // PC Execution Console State
  const [selectedDevice, setSelectedDevice] = useState<string>('');
  const [actionType, setActionType] = useState<ComputerActionType>('OBSERVE');
  const [commandParam, setCommandParam] = useState<string>('git status');
  const [isExecuting, setIsExecuting] = useState<boolean>(false);
  const [executionResult, setExecutionResult] = useState<ComputerExecutionResult | null>(null);
  const [stepProgress, setStepProgress] = useState<ComputerStepProgress[]>([]);
  const [requiresConfirmation, setRequiresConfirmation] = useState<boolean>(false);

  // Android State
  const [androidDevices, setAndroidDevices] = useState<AndroidDevice[]>([]);
  const [androidPairCode, setAndroidPairCode] = useState<string | null>(null);
  const [selectedAndroidId, setSelectedAndroidId] = useState<string | null>(null);
  const [androidContext, setAndroidContext] = useState<AndroidContextPayload | null>(null);
  const [tapX, setTapX] = useState<number>(540);
  const [tapY, setTapY] = useState<number>(1200);
  const [typeText, setTypeText] = useState<string>('');
  const [launchPackage, setLaunchPackage] = useState<string>('com.android.chrome');
  const [androidActionSuccess, setAndroidActionSuccess] = useState<string | null>(null);

  const fetchDevices = async () => {
    try {
      setLoading(true);
      const [pcList, androidList, stopStatus] = await Promise.all([
        apiClient.listPairedDevices().catch(() => []),
        apiClient.listAndroidDevices().catch(() => []),
        apiClient.getEmergencyStopStatus().catch(() => ({ is_emergency_stopped: false })),
      ]);

      setComputers(pcList);
      if (pcList.length > 0 && !selectedDevice) {
        setSelectedDevice(pcList[0].device_id);
      }

      setAndroidDevices(androidList);
      if (androidList.length > 0 && !selectedAndroidId) {
        setSelectedAndroidId(androidList[0].device_id);
        const ctx = await apiClient.getAndroidContext(androidList[0].device_id).catch(() => null);
        setAndroidContext(ctx);
      }

      setIsEmergencyStopped(stopStatus.is_emergency_stopped);
    } catch (err: any) {
      setError(err?.message || 'Failed to load paired devices.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDevices();
  }, []);

  const handleInitiatePairing = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDeviceName.trim()) return;

    setIsPairing(true);
    setError(null);
    try {
      const resp = await apiClient.initiateDevicePairing(newDeviceName, newDevicePlatform);
      setActivePairingData(resp);
      setInputPairingCode(resp.pairing_code);
    } catch (err: any) {
      setError(err?.message || 'Failed to initiate pairing.');
    } finally {
      setIsPairing(false);
    }
  };

  const handleConfirmPairing = async () => {
    if (!activePairingData || !inputPairingCode) return;

    setIsPairing(true);
    setError(null);
    try {
      await apiClient.confirmDevicePairing(activePairingData.device_id, inputPairingCode);
      setShowPairModal(false);
      setActivePairingData(null);
      setNewDeviceName('');
      await fetchDevices();
    } catch (err: any) {
      setError(err?.message || 'Invalid or expired pairing code.');
    } finally {
      setIsPairing(false);
    }
  };

  const handleRevokeDevice = async (deviceId: string) => {
    if (!confirm('Are you sure you want to revoke authorization for this computer?')) return;
    try {
      await apiClient.revokePairedDevice(deviceId);
      await fetchDevices();
    } catch (err: any) {
      setError(err?.message || 'Failed to revoke device.');
    }
  };

  const handleEmergencyStopToggle = async () => {
    try {
      if (isEmergencyStopped) {
        await apiClient.clearEmergencyStop();
        setIsEmergencyStopped(false);
      } else {
        await apiClient.triggerEmergencyStop();
        setIsEmergencyStopped(true);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to toggle emergency stop.');
    }
  };

  const handleExecute = async (confirmed = false) => {
    if (!selectedDevice) {
      setError('Please select an authorized computer first.');
      return;
    }

    setIsExecuting(true);
    setError(null);
    setRequiresConfirmation(false);

    try {
      const params: Record<string, any> = {};
      if (actionType === 'TERMINAL_RUN') {
        params.command = commandParam;
      } else if (actionType === 'CLICK') {
        params.x = 250;
        params.y = 180;
      } else if (actionType === 'TYPE') {
        params.text = commandParam;
      }

      const resp = await apiClient.executeComputerCommand(
        selectedDevice,
        actionType,
        params,
        confirmed
      );

      setExecutionResult(resp.result);
      setStepProgress(resp.steps);

      if (!resp.result.success && resp.result.output?.status === 'PENDING_APPROVAL') {
        setRequiresConfirmation(true);
      }
    } catch (err: any) {
      setError(err?.message || 'Computer execution failed.');
    } finally {
      setIsExecuting(false);
    }
  };

  // Android Companion Handlers
  const handleGenerateAndroidCode = async () => {
    try {
      const resp = await apiClient.generateAndroidPairingCode();
      setAndroidPairCode(resp.pairing_code);
    } catch (err: any) {
      setError(err?.message || 'Failed to generate Android pairing code.');
    }
  };

  const handleRevokeAndroid = async (deviceId: string) => {
    if (!confirm('Revoke authorization for this Android phone?')) return;
    try {
      await apiClient.revokeAndroidDevice(deviceId);
      await fetchDevices();
    } catch (err: any) {
      setError(err?.message || 'Failed to revoke Android device.');
    }
  };

  const handleAndroidAction = async (actionReq: AndroidActionRequest) => {
    if (!selectedAndroidId) return;
    setError(null);
    setAndroidActionSuccess(null);
    try {
      const res = await apiClient.dispatchAndroidAction(selectedAndroidId, actionReq);
      setAndroidActionSuccess(res.message);
    } catch (err: any) {
      setError(err?.message || 'Action dispatch failed');
    }
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header & Killswitch Bar */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-border pb-6">
          <div>
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-500">
                <Monitor className="w-7 h-7" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-foreground flex items-center gap-2">
                  Authorized Device & Bridge Control
                  <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 font-medium">
                    Live
                  </span>
                </h1>
                <p className="text-sm text-zinc-500">
                  PC Workstations, Android Companion Bridge, and 3-tier accessibility control loops.
                </p>
              </div>
            </div>
          </div>

          {/* Action Controls & Emergency Stop */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={handleEmergencyStopToggle}
              className={`px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all ${
                isEmergencyStopped
                  ? 'bg-amber-600 hover:bg-amber-500 text-white shadow-lg shadow-amber-900/30'
                  : 'bg-rose-600 hover:bg-rose-500 text-white shadow-lg shadow-rose-900/30 animate-pulse'
              }`}
            >
              <AlertOctagon className="w-4 h-4" />
              {isEmergencyStopped ? 'Resume Operations' : 'EMERGENCY STOP'}
            </button>

            {deviceTab === 'pc' ? (
              <button
                type="button"
                onClick={() => setShowPairModal(true)}
                className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-xs font-semibold text-white flex items-center gap-1.5 transition-colors shadow-lg shadow-cyan-900/20"
              >
                <Plus className="w-4 h-4" />
                Pair New PC
              </button>
            ) : (
              <button
                type="button"
                onClick={handleGenerateAndroidCode}
                className="px-4 py-2 rounded-xl bg-primary-600 hover:bg-primary-500 text-xs font-semibold text-white flex items-center gap-1.5 transition-colors shadow-lg shadow-primary-900/20"
              >
                <Key className="w-4 h-4" />
                Generate Phone Pairing Code
              </button>
            )}
          </div>
        </div>

        {/* Emergency Stop Banner */}
        {isEmergencyStopped && (
          <div className="p-4 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-300 flex items-center gap-3">
            <AlertOctagon className="w-6 h-6 text-rose-400 flex-shrink-0" />
            <div className="text-sm">
              <strong>Emergency Stop Active:</strong> All computer loops, mouse/keyboard inputs, and Android accessibility actions are halted immediately.
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0 text-rose-400 mt-0.5" />
            <div className="text-sm font-medium">{error}</div>
          </div>
        )}

        {androidActionSuccess && (
          <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 flex items-center gap-2 text-sm">
            <CheckCircle2 className="w-4 h-4" />
            {androidActionSuccess}
          </div>
        )}

        {/* Android Pairing Code Banner */}
        {androidPairCode && (
          <div className="p-5 rounded-xl border border-primary-500/40 bg-primary-500/5 flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                <Smartphone className="w-4 h-4 text-primary-500" />
                One-Time Android Companion Pairing Code
              </h3>
              <p className="text-xs text-zinc-500 mt-1">
                Enter this code in your Jenna Companion app on your phone. Code expires in 5 minutes.
              </p>
            </div>
            <div className="text-3xl font-mono font-bold tracking-widest text-primary-600 dark:text-primary-400 px-4 py-2 rounded-lg bg-card border border-border">
              {androidPairCode}
            </div>
          </div>
        )}

        {/* Tabs: PC vs Android */}
        <div className="flex border-b border-border gap-4">
          <button
            onClick={() => setDeviceTab('pc')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
              deviceTab === 'pc'
                ? 'border-cyan-500 text-cyan-600 dark:text-cyan-400'
                : 'border-transparent text-zinc-500 hover:text-foreground'
            }`}
          >
            <Monitor className="w-4 h-4" />
            Authorized Workstations ({computers.length})
          </button>
          <button
            onClick={() => setDeviceTab('android')}
            className={`pb-3 text-sm font-semibold flex items-center gap-2 border-b-2 transition-colors ${
              deviceTab === 'android'
                ? 'border-primary-500 text-primary-600 dark:text-primary-400'
                : 'border-transparent text-zinc-500 hover:text-foreground'
            }`}
          >
            <Smartphone className="w-4 h-4" />
            Android Companion Bridge ({androidDevices.length})
          </button>
        </div>

        {/* TAB 1: PC CONTROL */}
        {deviceTab === 'pc' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-5 space-y-4">
              <div className="rounded-2xl bg-card border border-border p-5 space-y-4">
                <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-cyan-500" />
                  Paired Computers ({computers.length})
                </h2>

                {loading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="w-6 h-6 animate-spin text-zinc-500" />
                  </div>
                ) : computers.length === 0 ? (
                  <div className="text-center py-8 text-zinc-500 space-y-2">
                    <Monitor className="w-8 h-8 mx-auto text-zinc-400" />
                    <p className="text-sm">No paired computers yet.</p>
                    <button
                      type="button"
                      onClick={() => setShowPairModal(true)}
                      className="text-xs text-cyan-500 hover:underline"
                    >
                      Pair your first workstation
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {computers.map((c) => (
                      <div
                        key={c.device_id}
                        onClick={() => setSelectedDevice(c.device_id)}
                        className={`p-4 rounded-xl border cursor-pointer transition-all ${
                          selectedDevice === c.device_id
                            ? 'bg-cyan-500/10 border-cyan-500/50 shadow-md shadow-cyan-950/20'
                            : 'bg-card border-border hover:border-zinc-400'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            <Monitor className="w-5 h-5 text-cyan-500" />
                            <div>
                              <div className="text-sm font-semibold text-foreground">{c.device_name}</div>
                              <div className="text-[11px] text-zinc-500 font-mono">{c.os_platform}</div>
                            </div>

                          </div>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRevokeDevice(c.device_id);
                            }}
                            className="p-1 text-zinc-400 hover:text-rose-400 transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* PC Execution Console */}
            <div className="lg:col-span-7 space-y-6">
              <div className="rounded-2xl bg-card border border-border p-6 space-y-6">
                <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-cyan-500" />
                  Computer Automation Console
                </h2>

                <div className="space-y-4">
                  <div className="grid grid-cols-3 gap-2">
                    {(['OBSERVE', 'TERMINAL_RUN', 'CLICK'] as ComputerActionType[]).map((type) => (
                      <button
                        key={type}
                        type="button"
                        onClick={() => setActionType(type)}
                        className={`py-2 rounded-xl text-xs font-semibold border transition-all ${
                          actionType === type
                            ? 'bg-cyan-500 text-white border-cyan-500'
                            : 'bg-card text-zinc-400 border-border hover:text-foreground'
                        }`}
                      >
                        {type}
                      </button>
                    ))}
                  </div>

                  <div className="space-y-2">
                    <label className="text-xs font-medium text-zinc-400">Parameter / Command</label>
                    <input
                      type="text"
                      value={commandParam}
                      onChange={(e) => setCommandParam(e.target.value)}
                      className="w-full px-3.5 py-2.5 rounded-xl bg-background border border-border text-sm text-foreground font-mono"
                    />
                  </div>

                  <button
                    type="button"
                    onClick={() => handleExecute(false)}
                    disabled={isExecuting || !selectedDevice}
                    className="w-full py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-semibold text-sm flex items-center justify-center gap-2 transition-colors"
                  >
                    {isExecuting ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                    Execute 6-Stage Loop
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: ANDROID COMPANION */}
        {deviceTab === 'android' && (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Left: Paired Phones List */}
            <div className="lg:col-span-5 space-y-4">
              <div className="rounded-2xl bg-card border border-border p-5 space-y-4">
                <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
                  <Smartphone className="w-4 h-4 text-primary-500" />
                  Linked Android Phones ({androidDevices.length})
                </h2>

                {androidDevices.length === 0 ? (
                  <div className="text-center py-8 text-zinc-500 space-y-2">
                    <Smartphone className="w-8 h-8 mx-auto text-zinc-400" />
                    <p className="text-sm">No phone paired yet.</p>
                    <button
                      type="button"
                      onClick={handleGenerateAndroidCode}
                      className="text-xs text-primary-500 hover:underline"
                    >
                      Generate pairing code to link phone
                    </button>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {androidDevices.map((dev) => (
                      <div
                        key={dev.device_id}
                        onClick={() => {
                          setSelectedAndroidId(dev.device_id);
                          apiClient.getAndroidContext(dev.device_id).then(setAndroidContext);
                        }}
                        className={`p-4 rounded-xl border cursor-pointer transition-all ${
                          selectedAndroidId === dev.device_id
                            ? 'bg-primary-500/10 border-primary-500/50 shadow-md shadow-primary-950/20'
                            : 'bg-card border-border hover:border-zinc-400'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2.5">
                            <Smartphone className="w-5 h-5 text-primary-500" />
                            <div>
                              <div className="text-sm font-semibold text-foreground">{dev.device_name}</div>
                              <div className="text-[11px] text-zinc-500">
                                {dev.model} • Android {dev.android_version}
                              </div>
                            </div>
                          </div>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRevokeAndroid(dev.device_id);
                            }}
                            className="p-1 text-zinc-400 hover:text-rose-400 transition-colors"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Context Viewer */}
              {androidContext && (
                <div className="rounded-2xl bg-card border border-border p-5 space-y-3">
                  <h3 className="text-xs font-semibold text-foreground uppercase tracking-wider">
                    Phone Telemetry & Screen State
                  </h3>
                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="p-2.5 rounded-lg bg-background border border-border flex items-center gap-2">
                      <Battery className="w-4 h-4 text-emerald-500" />
                      <span>{androidContext.battery_level}% {androidContext.is_charging ? '(Charging)' : ''}</span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-background border border-border flex items-center gap-2">
                      <Wifi className="w-4 h-4 text-blue-500" />
                      <span>{androidContext.network_type}</span>
                    </div>
                  </div>
                  <div className="text-xs text-zinc-500">
                    Foreground App: <strong className="text-foreground">{androidContext.foreground_app}</strong>
                  </div>
                </div>
              )}
            </div>

            {/* Right: Accessibility Gestures Console */}
            <div className="lg:col-span-7 space-y-6">
              <div className="rounded-2xl bg-card border border-border p-6 space-y-6">
                <h2 className="text-base font-semibold text-foreground flex items-center gap-2">
                  <Navigation className="w-4 h-4 text-primary-500" />
                  Authorized Accessibility Control
                </h2>

                <div className="space-y-5">
                  {/* System Navigation Buttons */}
                  <div>
                    <span className="text-xs font-medium text-zinc-400 block mb-2">Global Navigation</span>
                    <div className="grid grid-cols-4 gap-2">
                      {(['BACK', 'HOME', 'RECENTS', 'NOTIFICATIONS'] as const).map((nav) => (
                        <button
                          key={nav}
                          type="button"
                          onClick={() =>
                            handleAndroidAction({
                              action_type: 'NAVIGATE',
                              nav_target: nav,
                            })
                          }
                          className="py-2 text-xs font-semibold rounded-lg bg-background border border-border hover:bg-zinc-100 dark:hover:bg-zinc-800 text-foreground transition-colors"
                        >
                          {nav}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Tap at X, Y */}
                  <div className="p-4 rounded-xl border border-border bg-background/50 space-y-3">
                    <span className="text-xs font-semibold text-foreground">Tap Coordinate Gesture</span>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-[10px] text-zinc-400 block">X Coordinate (px)</label>
                        <input
                          type="number"
                          value={tapX}
                          onChange={(e) => setTapX(Number(e.target.value))}
                          className="w-full px-3 py-1.5 rounded bg-background border border-border text-xs text-foreground"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-zinc-400 block">Y Coordinate (px)</label>
                        <input
                          type="number"
                          value={tapY}
                          onChange={(e) => setTapY(Number(e.target.value))}
                          className="w-full px-3 py-1.5 rounded bg-background border border-border text-xs text-foreground"
                        />
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        handleAndroidAction({
                          action_type: 'TAP',
                          x: tapX,
                          y: tapY,
                        })
                      }
                      className="w-full py-2 rounded-lg bg-primary-600 hover:bg-primary-500 text-white font-semibold text-xs transition-colors"
                    >
                      Dispatch Tap Gesture
                    </button>
                  </div>

                  {/* Type Text */}
                  <div className="p-4 rounded-xl border border-border bg-background/50 space-y-3">
                    <span className="text-xs font-semibold text-foreground">Type Text into Focused Input</span>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Text to type..."
                        value={typeText}
                        onChange={(e) => setTypeText(e.target.value)}
                        className="flex-1 px-3 py-1.5 rounded bg-background border border-border text-xs text-foreground"
                      />
                      <button
                        type="button"
                        onClick={() =>
                          handleAndroidAction({
                            action_type: 'TYPE_TEXT',
                            text: typeText,
                            confirmed: true,
                          })
                        }
                        className="px-4 py-1.5 rounded-lg bg-primary-600 hover:bg-primary-500 text-white font-semibold text-xs transition-colors"
                      >
                        Type
                      </button>
                    </div>
                  </div>

                  {/* Launch App */}
                  <div className="p-4 rounded-xl border border-border bg-background/50 space-y-3">
                    <span className="text-xs font-semibold text-foreground">Launch Application Intent</span>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        placeholder="Package name (e.g. com.android.chrome)..."
                        value={launchPackage}
                        onChange={(e) => setLaunchPackage(e.target.value)}
                        className="flex-1 px-3 py-1.5 rounded bg-background border border-border text-xs text-foreground font-mono"
                      />
                      <button
                        type="button"
                        onClick={() =>
                          handleAndroidAction({
                            action_type: 'APP_LAUNCH',
                            package_name: launchPackage,
                            confirmed: true,
                          })
                        }
                        className="px-4 py-1.5 rounded-lg bg-primary-600 hover:bg-primary-500 text-white font-semibold text-xs transition-colors"
                      >
                        Launch
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
