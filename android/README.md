# 江山时序 Android 容器

这是使用 Java 和 Android 平台 WebView 的最小原生工程，没有 AndroidX 或第三方运行依赖。当前交付是源码工程；本环境没有 Java / Android SDK，未构建、未签名、未验证 APK，也没有下载工具链。

## 固定构建版本

| 工具 | 版本 |
| --- | --- |
| JDK | 17 |
| Gradle | 8.11.1 |
| Android Gradle Plugin | 8.9.2 |
| compileSdk / targetSdk | 35 / 35 |
| SDK Build Tools | 35.0.0 |
| minSdk | 23（Android 6.0） |

这些版本固定了可重复执行的构建环境；尚未证明 APK 字节级可重现。首次构建需联网下载 Gradle 插件和 SDK 依赖。Java 17 仅用于构建；手机无需安装 Java。

## 放入网页资源

把**已经完成的手机版静态构建目录的内容**复制到：

```text
android/app/src/main/assets/web/
  index.html
  ... JS、CSS、图片和数据文件
```

不要再套一层 dist/web 文件夹。网页构建的资源基路径应为 `./`，网页自己的链接、fetch、模块导入使用相对路径。容器会把 APK 内 `assets/web/index.html` 映射为 `https://appassets.androidplatform.net/assets/web/index.html`，所有本地资源通过 AssetManager 返回，不访问这个域名的远端服务器。使用 HTTPS 来源是为了正常运行 ES modules、fetch、localStorage，同时关闭 `file://` 和 `content://` 访问。`localStorage` 随应用数据保存，卸载或清除应用数据会丢失。

不要使用以 `/` 开头的资源地址：它会指向虚拟站点根目录，超出 `/assets/web/`。本地资源缺失返回 404，主页面加载失败显示错误提示和重新加载按钮；构建前也会检查 `index.html` 是否存在。此工程不生成占位 HTML，以免误把空壳打包。

PWA 的 Service Worker 不参与 APK 的资源提供；Android 的 `shouldInterceptRequest` 不接管 Service Worker 的所有网络请求。建议手机版检测虚拟域名 `appassets.androidplatform.net`，在容器中跳过 Service Worker 注册。PWA 在普通浏览器中仍可独立注册。离线可用程度取决于网页和已打包的数据；互联网地图瓦片等外部资源仍需联网。

## 使用已有 Gradle 构建

本工程没有携带 Gradle Wrapper 二进制或下载脚本。使用已安装的 **Gradle 8.11.1**，并设置 `JAVA_HOME` 指向 JDK 17、`ANDROID_HOME` 指向 Android SDK。SDK 安装 `platforms;android-35` 和 `build-tools;35.0.0`。也可在本目录创建不提交版本控制的 `local.properties`，设置本机 `sdk.dir`（Windows 推荐用正斜杠）。

在 `android` 目录执行：

```powershell
gradle --version
gradle --no-daemon --console=plain :app:assembleDebug :app:lintDebug
```

成功后 debug APK 位于 `app/build/outputs/apk/debug/app-debug.apk`，lint 报告位于 `app/build/reports/lint-results-debug.html`。需要设备安装测试时使用 Android Studio 或已有 adb：

```powershell
adb install -r app/build/outputs/apk/debug/app-debug.apk
```

Debug APK 由 Android 默认调试密钥签名，只适合测试。Release 构建未配置签名；正式分发前由项目维护者设置自己的 applicationId、版本、图标、签名与商店资料，密钥不要提交到 Git。

## 使用 Android Studio

使用支持 AGP 8.9 的 Android Studio（Meerkat 2024.3.1 或更新兼容版本）打开本目录。设置 Gradle JDK 为 17，Gradle distribution 为本地 Gradle 8.11.1；若 IDE 要求 Wrapper，可先使用已安装 Gradle 执行 `gradle wrapper --gradle-version 8.11.1 --distribution-type bin`，再由 IDE 使用生成的 Wrapper。SDK Manager 安装上述 SDK 版本后同步、选择 app，构建 Debug APK 或连接设备运行。第一次同步可能需要下载构建依赖；本交付没有进行这些操作。

## 可选 GitHub Actions 模板

`build-android.yml` 是模板，放在 Android 目录不会触发 Actions。用户可自行把它复制到仓库根目录 `.github/workflows/build-android.yml`，提交后从 Actions 页面手动运行。默认输入 `android_directory=android`，即假设仓库根目录是 `jiangshan-mobile`；如果把整个工作区作为仓库，请改为 `jiangshan-mobile/android`。

模板会在 GitHub 托管运行器上安装 JDK 17、Gradle 8.11.1 和指定 Android SDK，执行 assembleDebug / lintDebug，并上传 debug APK 和 lint HTML 作为该次运行的 artifact。网页静态资源必须已经在源码中正确准备完毕，否则构建明确失败；模板不替代网页构建。它不创建 Release、不上传应用商店、不配置正式签名，也不会自动推送。这里未运行工作流，模板中的 Actions 主版本标签还可由维护者按组织要求固定到审核后的 commit SHA。

## 容器边界和验收

- 唯一声明权限为 `INTERNET`，属于普通权限，用于 HTTPS 地图瓦片和在线数据，无位置、相机、麦克风、联系人或外部存储权限。
- JavaScript 与 DOM storage 开启；没有 JavaScript 到 Java 的桥接接口。文件、content 来源访问、跨文件来源访问、明文 HTTP 子资源及混合内容关闭，第三方 Cookie 关闭，地理定位关闭。
- 本地页面导航限定为虚拟 HTTPS 来源下 `/assets/web/` 路径；请求路径检查拒绝 `.`、`..`、反斜杠和 NUL。HTTP/HTTPS 外链导航交给系统浏览器，其余导航 scheme（file、content、javascript、intent 等）在原生导航回调中拒绝。
- Android WebView 不保证将网页自身 `javascript:` 伪链接交给原生导航回调。JavaScript 开启时，必须同时由网页避免此类链接或使用兼容的 CSP；不要将不可信 HTML 注入页面。导航拦截不等于关闭正常网页脚本。
- 返回键优先回退 WebView 历史，否则退出 Activity。主页面网络/HTTP/本地资源错误显示中文提示与重试按钮；子资源错误由网页自身处理，不会覆盖整个页面。缺失系统 WebView 提示更新组件。
- 未加入文件选择、下载、通知、后台定位、原生定位、弹窗窗口、支付或深链入口。这些若以后成为产品需求，需要单独设计。

具备 SDK 后至少验证：首次启动与旋转、年份切换和地图拖动、杀进程后 localStorage、无网络时页面与在线瓦片表现、外链浏览器跳转、拦截不支持的导航、返回键、主页面资源缺失重试。WebGL、地图性能以及 JavaScript 兼容性取决于设备 WebView 版本，需在真实 Android 设备测试。
