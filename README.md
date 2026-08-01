# 即梦 Seedance 白模上传器（Cinema 4D）

面向 **Cinema 4D 2026.3.1 / Windows** 的本地插件：使用 C4D 原生 **Viewport Renderer** 渲染白模动画为 H.264 MP4，并通过临时本机桥接将视频交给已登录的即梦网页导入。

> 这是非官方的个人项目，与 Maxon、即梦或 Seedance 没有隶属关系。即梦网页的交互方式可能随网页更新而变化。

## 功能

- 使用C4D的Viewport Renderer渲染白膜动画自动上传到即梦seedance。
- 渲染时临时切换到白模预设；完成后恢复原先的 Render Settings 和相机。
- 若当前使用其他 Render Settings，会将其输出宽高同步给白模预设；若已使用白模预设，则保留预设原有分辨率。
- 支持将已有的 H.264 MP4 通过本机桥接导入即梦网页。

## 运行要求

- Windows
- Cinema 4D 2026.3.1（当前测试版本）
- 支持 Viewport Renderer 的本机显卡与驱动
- 已在浏览器中登录即梦网页

Viewport Renderer 仅适用于本机渲染，不支持 Team Render。

## 安装

1. 在 [Releases](../../releases) 下载最新的 `jimeng_c4d_uploader-v*.zip`。
2. 解压 ZIP，得到 `jimeng_c4d_uploader` 文件夹。
3. 将整个文件夹复制到 Cinema 4D 的 `plugins` 目录，或在 C4D Preferences 中把该目录加入插件搜索路径。
4. 重启 Cinema 4D。
5. 从 **Extensions** 菜单打开“即梦 Seedance 白模上传器”。

安装后的目录应类似：

```text
plugins/
└─ jimeng_c4d_uploader/
   ├─ jimeng_c4d_uploader.pyp
   ├─ jimeng_c4d/
   └─ presets/
      └─ Jimeng Viewport White Model/
```

请保留 `presets` 目录；它包含插件所需的 Render Settings 预设。新电脑上不需要单独安装或导入预设。

## 使用方式

1. 先保存当前 `.c4d` 文件。插件会在渲染前检查；未保存时会要求使用 C4D 原生保存对话框保存场景。
2. 打开插件，在“相机”中选择用于导出的相机。
3. 点击“渲染设置”，在 C4D 原生 Render Settings 面板中检查或调整：
   - **Output**：帧范围、分辨率、帧率；
   - **Save**：保存位置、文件名和 MP4 / H.264；
   - **Viewport Renderer**：白模显示效果及过滤选项。
4. 需要恢复内置默认值时，点击“重置渲染设置”。这会完整恢复 `Jimeng Viewport White Model` 预设，但不会修改场景材质。
5. 点击“渲染并上传”。C4D 会使用 **Render to Picture Viewer** 输出视频；完成后插件会生成即梦链接。
6. 点击“打开即梦链接”，在已登录的浏览器中继续导入与创作。

## 本机桥接与隐私

插件只在本机启动临时 `localhost` 服务，让网页读取待导入的视频和默认提示词。该服务不会把视频保存到第三方中转服务器；链接在短时间内有效，并会在网页开始下载后自动关闭。

请只在自己信任的本机浏览器环境中使用该链接。即梦网页端的实际上传、账号状态和数据处理遵循其自身的服务规则。

## 视频与渲染限制

- 本地直传仅支持 H.264 / yuv420 的 `.mp4` 文件；MOV、WebM、AVI 不会被转码。
- 由插件渲染时，请在 C4D 的 **Save** 页面明确选择 MP4 与 H.264。
- 使用的帧范围、帧率、保存路径和文件名均以 `Jimeng Viewport White Model` Render Settings 为准。
- 该插件追求干净的 C4D 白模预览，不保证与 Blender Workbench、Redshift 或其他渲染器逐像素一致。

## 从源码构建

```powershell
git clone https://github.com/Aitidi/jimeng-c4d-uploader.git
cd jimeng-c4d-uploader
python -m unittest discover -s tests -v
PowerShell -NoProfile -ExecutionPolicy Bypass -File .\build_release.ps1
```

构建完成后，安装包位于 `dist/jimeng_c4d_uploader-v*.zip`。

## 反馈

提交问题时请说明 C4D 版本、Windows 版本、显卡 / 驱动、所选 Render Settings，以及 C4D Console 或插件状态栏中的错误信息。请勿提交 `.c4d` 项目文件、视频素材、登录信息或其他私人数据。

## 许可证

本仓库当前尚未提供开源许可证。除非获得明确授权，代码与资源默认保留所有权利。
