# BGPWatch-backend

### Install
```
pip3 install -r requirements
```

### Launch in Dev

run `app.py`

### Build
```
make build
```

### Generate Interface Document
```
make public_doc 
```

### Configuration
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

### Directory Tree

- config | configuration
- log | log file
- static ｜ static resource
- src ｜ source code
	- model ｜ DB Layer
	- service ｜ Interface Business Layer
	- view ｜ Interface Controller Layer
	- utils ｜ Utils