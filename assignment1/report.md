# Computer Networks Assignment 1

# About code

The ip and port inputed are not used, as dns.resolver.Resolver.resolve() actually doesn't need source and port(it use wildcard address by default, and it works well).

## LocalDNSServer
A quite simple UDP server, with a little thread pool to handle query concurrently.  

## DNSHandler
The most important part is function `query`. It's a recursive function, and I think comments and code is simple to read.

## CacheManager
A quite simple cache implementation, with a dict inside.
To provide thread safety, a read write lock from third party library is used.
If a cache is requested, manager will check whether the cache's expired first. If it's
expired, manager will delete the cache.
Manager will also clear expired cache in every 300s by default.

# Query results:
![](1.png)
![](2.png)
![](3.png)
![](4.png)
![](5.png)

The server can return queries stored in cache when received string "cache".  
I used nc to send command here.
![](6.png)
In cache above, query to github is about to expire. So, after a few seconds, it's not available.
![](7.png)
