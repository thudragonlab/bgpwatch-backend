# BGPWatch-backend
Providing API access interface for BGPWatch.

The BGPWatch platform has been developed by researchers and engineers from 19 countries/economies and funded by APNIC Foundation and the Chinese Government. The platform is accessible to the public at https://bgpwatch.cgtf.net.

The platform supports BGP hijack detection, provides swift response times, sends event warnings via email, assesses the severity of events, and provides event replay capabilities, which are all designed to effectively assist network operators. 

Additionally, the platform has developed various tools useful for network operators to monitor the network, including a dashboard displaying the key AS information, showing forward, reverse and bi-directional routing path.

### Install
```
pip3 install -r requirements
```

### Launch in Dev

run `app.py`

### Deploy
```
make build
```

### Generate Interface Documents
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

- config | Configuration
- log | Log File
- static ｜ Static Assests
- src ｜ Sources Code
	- model ｜ DB Layer
	- service ｜ Interface Business Layer
	- view ｜ Interface Controller Layer
	- utils ｜ Utils
