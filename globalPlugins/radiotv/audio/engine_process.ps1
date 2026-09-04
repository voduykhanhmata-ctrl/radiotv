# SPDX-License-Identifier: LGPL-2.1-or-later
# Copyright (c) 2026 Võ Duy Khánh

param(
    [Parameter(Mandatory = $true)]
    [string] $RuntimeDir,
    [Parameter(Mandatory = $true)]
    [string] $RequestId
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)

function Write-EngineMessage {
    param([hashtable] $Message)
    $Message.version = 1
    $Message.requestId = $RequestId
    [Console]::Out.WriteLine(($Message | ConvertTo-Json -Compress))
    [Console]::Out.Flush()
}

function Write-EngineError {
    param([string] $Code, [string] $Detail = "")
    Write-EngineMessage @{
        type = "error"
        code = $Code
        detail = $Detail
    }
}

function Resolve-InitialPlaybackRedirect {
    param(
        [Uri] $Uri,
        [string] $UserAgent
    )

    $response = $null
    try {
        $request = [System.Net.HttpWebRequest]::Create($Uri)
        $request.Method = "GET"
        $request.AllowAutoRedirect = $false
        $request.Timeout = 8000
        $request.ReadWriteTimeout = 8000
        $request.UserAgent = $UserAgent
        $response = [System.Net.HttpWebResponse] $request.GetResponse()
        $statusCode = [int] $response.StatusCode
        $location = [string] $response.Headers["Location"]
        if ($statusCode -lt 300 -or $statusCode -ge 400 -or
            [string]::IsNullOrWhiteSpace($location)) {
            return $Uri
        }
        $redirectedUri = [Uri]::new($Uri, $location)
        if (($redirectedUri.Scheme -ne "http" -and $redirectedUri.Scheme -ne "https") -or
            -not [string]::IsNullOrEmpty($redirectedUri.UserInfo)) {
            return $Uri
        }
        return $redirectedUri
    }
    catch {
        return $Uri
    }
    finally {
        if ($null -ne $response) {
            $response.Close()
        }
    }
}

function Invoke-WindowsMediaFallback {
    param(
        [Uri] $Uri,
        [int] $Volume,
        [string] $BassCode
    )

    $mediaPlayer = $null
    $mediaSource = $null
    try {
        $mediaPlayer = [Windows.Media.Playback.MediaPlayer, Windows.Media, ContentType = WindowsRuntime]::new()
        $mediaPlayer.Volume = [double] ($Volume / 100.0)
        $mediaSource = [Windows.Media.Core.MediaSource, Windows.Media, ContentType = WindowsRuntime]::CreateFromUri($Uri)
        $mediaPlayer.Source = $mediaSource
        $mediaPlayer.Play()

        $deadline = [DateTime]::UtcNow.AddSeconds(20)
        $lastState = ""
        $wasPlaying = $false
        while ($true) {
            $playbackState = [string] $mediaPlayer.PlaybackSession.PlaybackState
            if ($playbackState -eq "Playing") {
                if ($lastState -ne "Playing") {
                    Write-EngineMessage @{ type = "state"; state = "playing" }
                }
                $wasPlaying = $true
            }
            elseif ($playbackState -eq "Buffering" -or $playbackState -eq "Opening") {
                if ($lastState -ne $playbackState) {
                    Write-EngineMessage @{ type = "state"; state = "stalled" }
                }
            }
            elseif ($playbackState -eq "None" -and $wasPlaying) {
                Write-EngineMessage @{ type = "state"; state = "ended" }
                return $true
            }
            if (-not $wasPlaying -and [DateTime]::UtcNow -ge $deadline) {
                Write-EngineError "windows_media_timeout" ("bass=" + $BassCode)
                return $false
            }
            $lastState = $playbackState
            Start-Sleep -Milliseconds 200
        }
    }
    catch {
        Write-EngineError "windows_media_failed" (
            "bass=" + $BassCode + ";" + $_.Exception.GetType().Name
        )
        return $false
    }
    finally {
        if ($null -ne $mediaPlayer) {
            $mediaPlayer.Dispose()
        }
        if ($null -ne $mediaSource -and $mediaSource -is [IDisposable]) {
            $mediaSource.Dispose()
        }
    }
}

$stream = [uint32] 0
$bassInitialized = $false
$stage = "startup"

try {
    $stage = "runtime-files"
    $bassPath = Join-Path $RuntimeDir "bass.dll"
    $hlsPath = Join-Path $RuntimeDir "basshls.dll"
    if (-not (Test-Path -LiteralPath $bassPath -PathType Leaf)) {
        Write-EngineError "missing_bass"
        exit 2
    }
    if (-not (Test-Path -LiteralPath $hlsPath -PathType Leaf)) {
        Write-EngineError "missing_basshls"
        exit 2
    }

    $nativeSource = @"
using System;
using System.Runtime.InteropServices;

public static class RadioTvBassNative {
    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool SetDllDirectoryW(string path);

    [DllImport("bass.dll", CallingConvention = CallingConvention.StdCall, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool BASS_Init(int device, uint freq, uint flags, IntPtr win, IntPtr clsid);

    [DllImport("bass.dll", CallingConvention = CallingConvention.StdCall, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool BASS_SetConfig(uint option, uint value);

    [DllImport("bass.dll", EntryPoint = "BASS_PluginLoad", CharSet = CharSet.Unicode,
        CallingConvention = CallingConvention.StdCall, ExactSpelling = true)]
    public static extern uint BASS_PluginLoad(string file, uint flags);

    [DllImport("bass.dll", EntryPoint = "BASS_StreamCreateURL", CharSet = CharSet.Unicode,
        CallingConvention = CallingConvention.StdCall, ExactSpelling = true)]
    public static extern uint BASS_StreamCreateURL(
        string url, uint offset, uint flags, IntPtr downloadProc, IntPtr user);

    [DllImport("bass.dll", CallingConvention = CallingConvention.StdCall, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool BASS_ChannelSetAttribute(uint handle, uint attribute, float value);

    [DllImport("bass.dll", CallingConvention = CallingConvention.StdCall, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool BASS_ChannelPlay(uint handle, [MarshalAs(UnmanagedType.Bool)] bool restart);

    [DllImport("bass.dll", CallingConvention = CallingConvention.StdCall, ExactSpelling = true)]
    public static extern uint BASS_ChannelIsActive(uint handle);

    [DllImport("bass.dll", CallingConvention = CallingConvention.StdCall, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool BASS_StreamFree(uint handle);

    [DllImport("bass.dll", CallingConvention = CallingConvention.StdCall, ExactSpelling = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool BASS_Free();

    [DllImport("bass.dll", CallingConvention = CallingConvention.StdCall, ExactSpelling = true)]
    public static extern int BASS_ErrorGetCode();
}
"@

    $stage = "native-wrapper"
    Add-Type -TypeDefinition $nativeSource -Language CSharp | Out-Null
    $stage = "runtime-path"
    if (-not [RadioTvBassNative]::SetDllDirectoryW($RuntimeDir)) {
        Write-EngineError "runtime_path_failed"
        exit 2
    }

    $stage = "command"
    $rawCommand = [Console]::In.ReadLine()
    if ([string]::IsNullOrWhiteSpace($rawCommand)) {
        Write-EngineError "missing_command"
        exit 2
    }
    try {
        $command = $rawCommand | ConvertFrom-Json
    }
    catch {
        Write-EngineError "invalid_command_json"
        exit 2
    }
    if ($command.version -ne 1 -or $command.requestId -ne $RequestId) {
        Write-EngineError "command_mismatch"
        exit 2
    }
    $parsedUri = $null
    if (-not [Uri]::TryCreate([string] $command.url, [UriKind]::Absolute, [ref] $parsedUri)) {
        Write-EngineError "invalid_url"
        exit 2
    }
    if (($parsedUri.Scheme -ne "http" -and $parsedUri.Scheme -ne "https") -or
        -not [string]::IsNullOrEmpty($parsedUri.UserInfo)) {
        Write-EngineError "invalid_url"
        exit 2
    }
    $userAgent = [string] $command.userAgent
    if ([string]::IsNullOrWhiteSpace($userAgent)) {
        $userAgent = "RadioTV/0.1"
    }
    if ($userAgent.Length -gt 256 -or $userAgent.IndexOfAny([char[]] "`r`n") -ge 0) {
        Write-EngineError "invalid_user_agent"
        exit 2
    }
    foreach ($character in $userAgent.ToCharArray()) {
        if ([int] $character -lt 32 -or [int] $character -eq 127) {
            Write-EngineError "invalid_user_agent"
            exit 2
        }
    }
    $volume = 0
    if (-not [int]::TryParse([string] $command.volume, [ref] $volume) -or
        $volume -lt 0 -or $volume -gt 100) {
        Write-EngineError "invalid_volume"
        exit 2
    }

    $stage = "bass-init"
    if (-not [RadioTvBassNative]::BASS_Init(-1, 44100, 0, [IntPtr]::Zero, [IntPtr]::Zero)) {
        Write-EngineError "bass_init_failed" ([string] [RadioTvBassNative]::BASS_ErrorGetCode())
        exit 3
    }
    $bassInitialized = $true
    [RadioTvBassNative]::BASS_SetConfig(11, 8000) | Out-Null
    [RadioTvBassNative]::BASS_SetConfig(21, 1) | Out-Null
    [RadioTvBassNative]::BASS_SetConfig(37, 8000) | Out-Null

    $unicodeFlag = [Convert]::ToUInt32("80000000", 16)
    $stage = "basshls-load"
    $plugin = [RadioTvBassNative]::BASS_PluginLoad($hlsPath, $unicodeFlag)
    if ($plugin -eq 0) {
        Write-EngineError "basshls_load_failed" ([string] [RadioTvBassNative]::BASS_ErrorGetCode())
        exit 3
    }
    Write-EngineMessage @{ type = "ready" }

    $stage = "stream-open"
    $playbackUri = $parsedUri
    $requestTarget = $playbackUri.AbsoluteUri + "`r`nUser-Agent: " + $userAgent + "`r`n"
    $stream = [RadioTvBassNative]::BASS_StreamCreateURL(
        $requestTarget,
        0,
        $unicodeFlag,
        [IntPtr]::Zero,
        [IntPtr]::Zero
    )
    if ($stream -eq 0) {
        $bassCode = [string] [RadioTvBassNative]::BASS_ErrorGetCode()
        $redirectedUri = Resolve-InitialPlaybackRedirect $playbackUri $userAgent
        if ($redirectedUri.AbsoluteUri -ne $playbackUri.AbsoluteUri) {
            $playbackUri = $redirectedUri
            $requestTarget = $playbackUri.AbsoluteUri + "`r`nUser-Agent: " + $userAgent + "`r`n"
            $stream = [RadioTvBassNative]::BASS_StreamCreateURL(
                $requestTarget,
                0,
                $unicodeFlag,
                [IntPtr]::Zero,
                [IntPtr]::Zero
            )
            if ($stream -eq 0) {
                $bassCode = [string] [RadioTvBassNative]::BASS_ErrorGetCode()
            }
        }
        if ($stream -eq 0 -and (Invoke-WindowsMediaFallback $playbackUri $volume $bassCode)) {
            exit 0
        }
        if ($stream -eq 0) {
            exit 4
        }
    }
    $stage = "volume"
    $volumeLevel = [single] ($volume / 100.0)
    if (-not [RadioTvBassNative]::BASS_ChannelSetAttribute($stream, 2, $volumeLevel)) {
        Write-EngineError "volume_failed" ([string] [RadioTvBassNative]::BASS_ErrorGetCode())
        exit 4
    }
    $stage = "channel-play"
    if (-not [RadioTvBassNative]::BASS_ChannelPlay($stream, $false)) {
        Write-EngineError "play_failed" ([string] [RadioTvBassNative]::BASS_ErrorGetCode())
        exit 4
    }

    $stage = "playback-monitor"
    $deadline = [DateTime]::UtcNow.AddSeconds(15)
    $lastState = [uint32]::MaxValue
    $wasPlaying = $false
    while ($true) {
        $active = [RadioTvBassNative]::BASS_ChannelIsActive($stream)
        if ($active -eq 1) {
            if ($lastState -ne 1) {
                Write-EngineMessage @{ type = "state"; state = "playing" }
            }
            $wasPlaying = $true
        }
        elseif ($active -eq 2) {
            if ($lastState -ne 2) {
                Write-EngineMessage @{ type = "state"; state = "stalled" }
            }
        }
        elseif ($active -eq 0) {
            if ($wasPlaying) {
                Write-EngineMessage @{ type = "state"; state = "ended" }
                exit 0
            }
            $bassCode = [string] [RadioTvBassNative]::BASS_ErrorGetCode()
            [RadioTvBassNative]::BASS_StreamFree($stream) | Out-Null
            $stream = [uint32] 0
            if (Invoke-WindowsMediaFallback $playbackUri $volume $bassCode) {
                exit 0
            }
            exit 4
        }
        if (-not $wasPlaying -and [DateTime]::UtcNow -ge $deadline) {
            Write-EngineError "playback_confirmation_timeout"
            exit 4
        }
        $lastState = $active
        Start-Sleep -Milliseconds 200
    }
}
catch {
    Write-EngineError "worker_exception" (
        $stage + ":" + $_.Exception.GetType().Name
    )
    exit 5
}
finally {
    if ($stream -ne 0) {
        [RadioTvBassNative]::BASS_StreamFree($stream) | Out-Null
    }
    if ($bassInitialized) {
        [RadioTvBassNative]::BASS_Free() | Out-Null
    }
}
