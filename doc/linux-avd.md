# Linux Android AVD 按需启停

SRC 可以在 Linux 上按任务需要启动和关闭 Android SDK 官方 Emulator 的 AVD。Windows、macOS、实体设备和其他模拟器仍使用原有行为；它们的 Web 配置页不会显示此功能。

## 生命周期

选择 `AndroidAVD` 后，未来任务不会初始化 `Device` 或启动 AVD。任务到期时，SRC 启动指定 AVD，并按顺序确认：

1. AVD 名称和控制台端口匹配的模拟器进程存在；
2. 指定 ADB serial 的状态为 `device`；
3. `sys.boot_completed=1`；
4. ADB shell 可以执行命令；
5. Android package manager 可用。

所有当前已到期的任务共用同一个 `Device`。任务队列进入等待后，SRC 先运行原有的游戏退出逻辑，再发送 `adb emu kill`，并等待 ADB serial 和精确匹配的进程全部消失。启动超时、部分 `Device` 初始化、任务异常、`SystemExit`、SIGTERM 和 Web UI 手动停止都会尝试清理 AVD。

启动和关闭使用单调时钟与轮询，不用固定 sleep 推断 Android 是否启动完成。为避免误关其他 AVD，只有找到配置名称和端口对应的进程时才会向 serial 发送 `adb emu kill`；超时后的 TERM/KILL 也只作用于精确匹配的进程。

## 配置

先使用 Android SDK 的 `avdmanager` 创建 AVD，再在 SRC 的 `Alas` 配置页选择 `AndroidAVD`。只有选择该模拟器后，页面才显示 `LinuxAVD` 设置。

| 设置 | 示例 | 说明 |
| --- | --- | --- |
| `Emulator.Serial` | `emulator-5554` | 端口必须是 5554 至 5682 范围内的偶数 |
| `EmulatorInfo.Emulator` | `AndroidAVD` | 启用 Linux AVD 生命周期 |
| `EmulatorInfo.name` | `src-cloud` | 已创建的 AVD 名称 |
| `EmulatorInfo.path` | `/opt/android-sdk/emulator/emulator` | 可留空并从 SDK 根目录或环境变量解析 |
| `LinuxAVD.SDKRoot` | `/opt/android-sdk` | 可留空并使用 `ANDROID_SDK_ROOT` 或 `ANDROID_HOME` |
| `LinuxAVD.AdbPath` | `/opt/android-sdk/platform-tools/adb` | 可留空并从 SDK 根目录或 `PATH` 解析 |
| `LinuxAVD.MemoryMB` | `2048` | 有效范围为 1536 至 8192 MB |
| `LinuxAVD.GPU` | `host` | 可选 `host`、`auto` 或 SwiftShader 模式 |
| `LinuxAVD.Headless` | `true` | 首次安装和登录时可设为 `false` |
| `LinuxAVD.StartTimeout` | `300` | 五个启动阶段共用的总超时，单位秒 |
| `LinuxAVD.StopTimeout` | `60` | 等待 serial 和进程消失的时间，单位秒 |

要在任务间关闭 AVD，还需要把 `Optimization.WhenTaskQueueEmpty` 设为 `close_emulator`。每个并行运行的 SRC 配置应使用不同的 AVD 名称和 ADB serial，避免两个调度器控制同一个 Android 实例。

## 数据持久化

启动命令不会包含 `-wipe-data`、临时 `-data` 路径或其他丢弃 userdata 的选项。正常关闭不会删除应用和登录数据。

首次使用建议把 `LinuxAVD.Headless` 设为 `false`，在可见窗口中由用户本人安装应用、登录并授予权限。确认关闭和重启后数据仍存在，再启用无窗口运行。不要把账号、验证码或登录数据写入 SRC 配置、日志或 Git。

## 故障定位

日志会记录 `process`、`adb_serial`、`boot_completed`、`adb_shell` 和 `package_manager` 阶段。常用检查命令：

```bash
$ANDROID_SDK_ROOT/emulator/emulator -accel-check
$ANDROID_SDK_ROOT/platform-tools/adb devices
$ANDROID_SDK_ROOT/platform-tools/adb -s emulator-5554 shell getprop sys.boot_completed
```

如果启动失败，先检查 AVD 是否存在、KVM 权限、SDK 路径、端口占用和 GPU 驱动。若日志提示 serial 在线但没有精确匹配的进程，应先解决端口冲突；SRC 会拒绝关闭无法确认归属的 AVD。
