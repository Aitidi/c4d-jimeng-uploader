# 即梦 Seedance 白模上传器（C4D 2026.3.1）

此插件使用 Cinema 4D 的 **Viewport Renderer** 直接输出 MP4 白模动画，再通过本机临时桥接交给即梦网页导入。

## 安装

1. 将整个 `jimeng_c4d_uploader` 文件夹（包括其中的 `presets` 子目录）复制到 Cinema 4D 2026 的 `plugins` 目录。
2. 重启 Cinema 4D。
3. 从 Extensions 菜单打开“Seedance_c4d_uploader”。
4. 首次打开会从插件内置的 `presets/Jimeng Viewport White Model` 导入 `Jimeng Viewport White Model` Render Settings 到当前 `.c4d` 文件。


## 使用

1. 选择相机。`Jimeng Viewport White Model` 是固定的唯一 Render Settings；帧范围、帧率和 Save 路径均自动读取该设置。仅在点击渲染时、当前设置不是 Jimeng 预设的情况下，插件会同步当前设置的输出宽高。
2. 点击“渲染设置”会将它设为 C4D 当前设置并打开原生 **Edit Render Settings** 面板。需要修改时直接在此处调整 Output、Save、Viewport Renderer 等选项。
3. 点击“重置渲染设置”会从上述 Asset Browser 预设完整恢复参数，包括 Save 路径和自动文件名；不会添加材质覆盖、效果或其他渲染模块。
4. 点击“渲染并上传”。如果当前 `.c4d` 尚未保存，插件会先提示并打开 C4D 原生保存对话框；取消保存则不会开始渲染。保存后，如果当前 Render Settings 不是 `Jimeng Viewport White Model`，插件会先将当前设置的 Output 宽高同步到 Jimeng 预设，再临时切换到该预设并调用 C4D 原生 **Render to Picture Viewer**（不是 Alt+B 的 Make Preview）。若当前已是 Jimeng 预设，则保持其原有宽高。C4D 完成 MP4 写入后，插件会恢复原 Render Settings 和相机，再上传。
5. 点击“打开即梦链接”。链接依赖本机临时 HTTP 服务：30 分钟后失效，网页开始下载后 60 秒关闭。

## 依赖与限制
- Viewport Renderer 仅支持本机渲染，不能经 Team Render 分发。
- 即梦网页协议和 localhost 跨域策略为外部未公开接口，网页改版后可能需要调整桥接逻辑。

