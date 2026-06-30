# ZombieGoDie

用手势消灭僵尸的摄像头控制游戏。

## 环境要求

- Python 3.9+
- 摄像头（Mac 内置摄像头即可）

## 安装

```bash
pip3 install -r requirements.txt
```

## 运行

```bash
python3 main.py
```

## 手势操作

| 手势 | 技能 | 效果 | 冷却 |
|---|---|---|---|
| ✊ 拳头 | 冲击波 | 消灭左1/3屏幕内所有僵尸 | 3秒 |
| ☝ 食指 | 精准射击 | 高伤害子弹直线飞行 | 1秒 |
| ✋ 张开手掌 | 冰冻术 | 所有僵尸减速50%持续3秒 | 5秒 |
| ✌ 剪刀手 | 双线激光 | 两条水平激光持续0.5秒 | 2秒 |
| 👍 大拇指 | 投弹 | 延迟0.8秒范围爆炸 | 4秒 |

## 按键

- `ESC` — 退出
- `R` — 游戏结束后重新开始

## 手势测试

单独运行手势识别调试窗口：

```bash
python3 gesture/test_gesture.py
```

## 项目结构

```
zombieGoDie/
├── main.py          # 游戏入口
├── config.py        # 全局配置
├── gesture/         # 手势识别模块
│   ├── detector.py  # MediaPipe 封装
│   └── classifier.py# 关键点→手势判定+防抖
└── game/            # 游戏逻辑
    ├── scene.py     # 主场景
    ├── zombie.py    # 僵尸实体
    ├── attack.py    # 5种攻击技能
    ├── player.py    # 玩家状态
    └── hud.py       # UI渲染
```
