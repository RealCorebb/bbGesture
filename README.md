# bbGesture [English](https://github.com/RealCorebb/bbGesture/blob/main/README_EN.md "English")

![image](https://github.com/RealCorebb/bbGesture/blob/main/IMG/bbGesture.jpg?raw=true)

## 可穿透物体的隔空手势传感器

我以前做过支持手势交互的嵌入式作品，但市面上普遍的光学手势传感器需外露，影响美观。如今，我动手制作了一款可穿透物体的手势传感器，可以隔着物体隔空检测到手并识别手势动作，甚至支持 3D 定位。

😄[爱发电](https://afdian.com/a/kuruibb "爱发电")  （已更新此图文教程）  
🐧QQ 群（仅供交流）：647186542  
🐦[Twitter](https://twitter.com/RealCorebb "@RealCorebb") @RealCorebb  
🧵[Threads](https://www.threads.net/@coreoobb "@coreoobb") @coreoobb  
▶️ 本期视频(Video): [Youtube](https://youtu.be/Or8UPq3nDdc "Youtube") | [ Bilibili](https://www.bilibili.com/video/BV1r6PceuEDK " Bilibili")

# 禁止搬运到 Gitee

Designed By Corebb With Love From bbRealm!

# 目录结构：

**Arduino** Arduino 示例程序，用于单片机使用该手势传感器的场景  
**Libs** Arduino 库，基于 DFRobot 的库修改而来 https://github.com/DFRobot/DFRobot_MGC3130  
**PC_Tools** PC 端的 DEMO 应用软件  
**PCB** PCB 原理图、Gerber 制板文件、BOM

# 参考资料：

芯片是 Microchip 的 MGC3130  
https://www.microchip.com/en-us/products/touch-and-gesture/3d-gestures/gestic-technology-basics　　
官方的硬件参考设计（内含USB转I²C模块）
https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ProductDocuments/BoardDesignFiles/GestICHardwareReferencesV1.0.5.zip
