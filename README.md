# d2-ruin-farm-remake
d2-ruin-farm-remake



git:
https://github.com/bffwy/d2-ruin-farm-remake

百度云：
链接：https://pan.baidu.com/s/1_ciG1dNqVBQUg_WcftwM-g
提取码：q9jv

微云：
链接：https://share.weiyun.com/rpB4pEbL 密码：9tzpm4


使用说明：
setting：

1. 使用DIM功能配置 看前面的视频, 默认关闭
    1.1 增加装备过滤
        护甲属性
        过滤武器

2. 开启log窗口配置 默认开启
3. exe 开启会先检测一下功能是否正常
4. 修改 task_config.json 可以改各个任务的配置
5. 适配不同的分辨率，先截取对应的图片，覆盖到asset的图片 然后删除自己电脑分辨率的图片，
    重新打开 exe 就会生效


根据类型解释一下act配置
key == 按住某个键
    duration: 按住的时间(s)

mouse_move == 鼠标移动
    relative: 相对坐标 [x, y]
        加大 x  == 右移动； 减小 x == 往左移
        加大 y == 往下移动  减小 y == 往上移动

    absolute: 绝对坐标 [x, y] == 鼠标直接移动到这个坐标点
        base_on_2560：
            true: 如果屏幕不是 2560 * 1440，则会将坐标等比例换算
            false: 不换算，写的是什么就移动到那里
        如果不改坐标也能运行，就是true
        如果要改成你本机的坐标的话，就是false

wait == 等待
    duration: 等待时间(s)

leftClick == 鼠标左键点击

rightClick == 鼠标右键点击

mouseDown == 按下鼠标的某个键
    key：left / right == 按住鼠标左键 / 右键

mouseUp == 松开鼠标的某个键
    key：left / right == 按住鼠标左键 / 右键

press == 点击某个键
    key：按的键
    比如
    {
        "type": "press",
        "key": "3"
    }
    就是按下 3 这个键

action == "调用其它的act配置文件"
    为什么会有这个？
    比如 开局都有一个共同的射击boss，
    这部分共同的就可以抽象为一个公用的action
    当然你可以不使用这个，那就是一个文件写完所有的行为即可

通用参数：
blocking：
当设置为false的时候，并且这个action有duration的话
就不会等待它执行完成，而是直接往下执行
比如你再跑向怪终结的时候，这个时候是同时按住 v + shift + w的，这个时候就需要设置为false
