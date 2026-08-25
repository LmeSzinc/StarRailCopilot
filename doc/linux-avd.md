# Linux AVD 按需启停

SRC 支持常驻运行，而 Android Emulator AVD 仅在任务到期时运行。它适用于 Linux 上的官方 Android Emulator；Windows、实体设备和其他模拟器维持原有行为。

## 工作方式

选择 `AndroidAVD` 后，SRC 会在首次创建 Device 之前启动指定 AVD，并按顺序轮询：

1. 精确匹配的模拟器进程；
2. 指定 ADB serial 的状态为 `device`；
3. `sys.boot_completed=1`；
4. ADB shell 可执行命令；
5. Android package manager 可用。

任务到期前不会读取惰性的 Device 属性，所以空闲启动 SRC 不会启动 AVD。所有已经到期的任务共用同一个 Device；遇到下一项未来任务时，SRC 先运行原有的云游戏退出逻辑，再执行 `adb emu kill`，并等待 ADB serial 和模拟器进程均消失。启动超时、Device 初始化失败、任务异常、`SystemExit` 和 Linux GUI 手动停止都会尝试走同一清理路径。

启动和关闭使用单调时钟、轮询和总超时，不用固定 sleep 猜测开机状态。

## SRC 配置

在 SRC 配置页填写：

| 设置 | 建议值 | 说明 |
| --- | --- | --- |
| `Emulator.Serial` | `emulator-5554` | 必须是 5554–5682 范围内的偶数控制台端口 |
| `EmulatorInfo.Emulator` | `AndroidAVD` | 只有这个值会启用 Linux AVD 生命周期 |
| `EmulatorInfo.name` | `src-cloud` | `avdmanager` 创建的 AVD 名称 |
| `EmulatorInfo.path` | SDK 中的 `emulator/emulator` | 可留空，由 SDK 根目录或环境变量解析 |
| `LinuxAVD.SDKRoot` | Android SDK 根目录 | 可留空并使用 `ANDROID_SDK_ROOT`/`ANDROID_HOME` |
| `LinuxAVD.AdbPath` | SDK 中的 `platform-tools/adb` | 可留空自动解析 |
| `LinuxAVD.MemoryMB` | `2048` | 稳定后可试 `1536`，不建议直接降得更低 |
| `LinuxAVD.GPU` | `host` | 使用宿主机 GPU；软件渲染仅用于排障 |
| `LinuxAVD.Headless` | 首次 `false`，日常 `true` | 首次显示窗口以便安装和登录 |
| `LinuxAVD.StartTimeout` | `300` | 整个五阶段启动的总超时，单位秒 |
| `LinuxAVD.StopTimeout` | `60` | 等待 ADB 和进程消失的宽限时间，单位秒 |

同时把 `Optimization.WhenTaskQueueEmpty` 设为 `close_emulator`。云游戏继续使用原有的 `cloud_android` 和服务器设置，登录、排队及任务代码不需要修改。

## 首次有窗口安装和登录

1. 先把 `LinuxAVD.Headless` 设为 `false`。
2. 启动一个到期任务，或在终端用同一 AVD、serial、内存和 GPU 参数启动模拟器。
3. 只从可信来源安装云游戏 APK，在模拟器窗口中由用户本人输入账号、验证码并完成授权。
4. 关闭 AVD 后再次启动，确认应用、登录状态和授权仍存在。
5. 无人值守运行前把 `Headless` 改为 `true`。

启动参数不会包含 `-wipe-data`、临时 `-data` 或其他清除 userdata 的选项。正常 `adb emu kill` 不会删除 AVD，应用和登录数据保存在 AVD 的 userdata 中。宿主机突然断电仍可能损坏任何正在写入的虚拟磁盘，建议备份 `~/.android/avd/src-cloud.avd`。

登录凭据和验证码不应写入 SRC 配置、日志、Git 或自动化脚本。

## 故障定位

日志会显示 `process`、`adb_serial`、`boot_completed`、`adb_shell`、`package_manager` 五个阶段以及超时清理动作。常见检查：

```bash
$ANDROID_SDK_ROOT/emulator/emulator -accel-check
$ANDROID_SDK_ROOT/platform-tools/adb devices
$ANDROID_SDK_ROOT/platform-tools/adb -s emulator-5554 shell getprop sys.boot_completed
```

如果 `-gpu host` 无法启动，先检查 KVM 权限、Mesa/EGL/Vulkan 驱动和当前图形会话。不要直接长期切换到软件渲染；老 CPU 上软件渲染通常会显著降低云游戏可用性。
