# BGPWatch-backend
为BGPWatch前端提供API访问接口

BGPWatch平台由来自19个国家/经济体的研究人员和工程师开发，由APNIC基金会和中国政府资助。公开网址为https://bgpwatch.cgtf.net.

该平台支持BGP劫持检测，确保快速响应时间，通过电子邮件发送事件警告，评估事件的严重性，并提供事件回放功能，所有这些都旨在有效协助网络运营商。

此外，该平台还开发了各种可供网络运营商监控网络的工具，包括显示关键AS信息的仪表板，显示正向、反向和双向路由路径，以及支持订阅。

### 安装
```
pip3 install -r requirements
```

### 开发环境运行

运行 `app.py`

### 部署
```
make build
```

### 生成接口文档
```
make public_doc
```

### 配置文件
```
{  
"db": [{  
    "host": "xxxx",  
    "port": 17017,  
    "user": "xxxx",  
    "pwd": "xxx"  
  },{  
    "host": "xxxx",  
    "port": 17017,  
    "user": "xxxx",  
    "pwd": "xxxx"  
  }]
}
```

### 目录结构

- config | 配置
- log | 日志文件
- static ｜ 静态资源
- src ｜ 源代码
	- model ｜ 数据库操作层
	- service ｜ 接口业务层
	- view ｜ 接口控制层
	- utils ｜ 工具类