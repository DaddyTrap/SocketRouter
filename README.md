# SocketRouter

基于Socket来进行虚拟路由

## 运行测试

```bash
# 在项目根目录
python3 -m tests.five_node_test LS
python3 -m tests.five_node_test DV
```

## 结点配置文件

```plain
{
  "name": String,
  "node_id": Number,
  "ip": "$ip",
  "port": $port,
  "topo": {
    "$node_id": {
      "real_ip": "$ip",
      "real_port": $port,
      "cost": Number
    }
  }
}
```

## 协议

换行符使用 `\n` 而非 `\r\n`

基本协议形式

```plain
SRC_ID $源结点NODE_ID
DST_ID $目标结点NODE_ID，-1表示广播 $序列号，如果是广播需要序列号进行受控洪泛
$数据包类型(DATA/ROUTE/BEAT) $携带数据类型(TXT/JPEG/PNG/...)/$使用的算法模式(LS/DV)/$心跳(BEAT)
$数据，支持二进制
```

### DATA类型

文本：
```plain
SRC_ID 0
DST_ID 1
DATA TXT
Hello world, and this is the raw text data.
Feel free to use \n or \r\n here. It only depends on your application.
甚至可以写中文。
```

图片：
```plain
SRC_ID 0
DST_ID 1
DATA PNG
[Here should be the binary data]
```

### ROUTE类型

#### LS模式路由信息

广播自身的邻居情况：
```plain
SRC_ID 0
DST_ID -1 132
ROUTE LS
$NODE_ID_0 $LINK_COST_0
$NDOE_ID_1 $LINK_COST_1
...
```

#### DV模式路由信息

向邻居发送自身的邻居情况
```plain
SRC_ID 0
DST_ID 1
ROUTE DV
$NODE_ID_0 $LINK_COST_0
$NDOE_ID_1 $LINK_COST_1
...
```

#### 请求路由信息

向邻居发送路由信息请求
```plain
SRC_ID 0
DST_ID 1
ROUTE REQ
REQ
```

### BEAT类型

广播心跳信息：
```plain
SRC_ID 0
DST_ID -1 123
BEAT BEAT
ALIVE
```