# BGPWatch-backend

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