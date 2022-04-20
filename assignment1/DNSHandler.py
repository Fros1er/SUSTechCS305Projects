from xml import dom
import dns
from typing import List, Tuple, Dict
from dns import resolver, rdatatype, message, rrset
from CacheManager import CacheManager


class DNSHandler():

    cache: CacheManager
    # Cache stores List[dns.rrset.RRset] for query, Dict[str, str] for root

    def __init__(self):
        super().__init__()
        self.cache = CacheManager()
        # query root once to store it in cache
        self.queryRoot()

    def handle(self, msg: bytes) -> bytes:
        """
        Receive dns message from dig and return results.
        """
        # Parse message from socket
        try:
            queryMessage: message.Message = message.from_wire(msg)
        except Exception:
            # If query message is invalid, try parse message as command
            command = msg.decode().strip('\n').strip()
            if (command == "cache"):
                return str(self.cache).encode()
            return b""

        domainName: str = queryMessage.question[0].to_text().split(' ')[0]
        try:
            res, _ = self.query(domainName, rdatatype.A, self.queryRoot(), True)
        except (resolver.NoNameservers, resolver.NXDOMAIN):
            # These two exceptions means no result and should be write into cache. ttl is by default 3600s.
            self.cache.writeCache(
                str(rdatatype.A) + " " + dns.name.from_text(domainName).to_text(), [], 3600)
            res = []
        except dns.exception.DNSException as e:
            print(e)
            res = []
        queryMessage.answer = res

        return queryMessage.to_wire()

    def resolve(self, qname: str, rdtype: rdatatype.RdataType, nameServers: List[str], raiseOnNoAns=False) -> resolver.Answer:
        """
        A simple wrap for Resolver.resolve.
        """
        # Instantiate dns.resolver.Resolver and set flag (value of rd) as 0.
        dnsResolver = resolver.Resolver()
        dnsResolver.flags = 0x0000
        # Set nameservers of dns_resolver as list of IP address of server.
        dnsResolver.nameservers = nameServers
        # Do query
        return dnsResolver.resolve(qname, rdtype, raise_on_no_answer=raiseOnNoAns)

    def query(self, domain: str, rdtype: rdatatype.RdataType, nameServers: Dict[str, List[str]], writeCache: bool = False) -> Tuple[List[rrset.RRset], int]:
        """
        Do the dns query process.
        If cache is present, return from cache directly.
        nameServers are parsed in the form of {domainName : [ip, ip...]}.
        Query is a recursive function, each time it get result from itself,
        it will concat the results together and update the ttl.
        writeCache is used to identify whether this query is the first query 
        for a fresh domain name, to ensure all the records can be stored in 
        the cache.
        """
        # parse name
        qname = dns.name.from_text(domain)

        # check from cache
        cacheKey = str(rdtype) + " " + qname.to_text()
        cache = self.cache.readCache(cacheKey)
        if cache is not None:
            print("read from cache")
            return cache

        # parse nameServers dict
        ns = []
        for name in nameServers:
            for ip in nameServers[name]:
                ns.append(ip)

        # do query
        ans = self.resolve(qname, rdtype, ns)
        res = ans.response

        hasAuthority = False
        hasCNAME = False

        # in case of answer returns A:
        if ans.rrset is not None:
            if writeCache:
                self.cache.writeCache(cacheKey, res.answer, ans.rrset.ttl)
            return res.answer, ans.rrset.ttl

        # in case of answer contains authority:
        if len(res.authority) > 0:
            hasAuthority = True
            hasAuthorityIp = False
            # initialize nameservers dict
            nsDict: Dict[str, List[str]] = {}
            for rrset in res.authority:
                if rrset.rdtype == rdatatype.NS:
                    for row in rrset:
                        nsDict[row.to_text()] = []

            # Get nameservers ip from existed nameservers
            for name in nameServers:
                if name in nsDict and len(nameServers[name]) != 0:
                    nsDict[name] = nameServers[name]
                    hasAuthorityIp = True

            # Get nameservers ip from additional
            for rrset in res.additional:
                name = rrset.name.to_text()
                if rrset.rdtype == rdatatype.A or rrset.rdtype == rdatatype.AAAA and name in nsDict:
                    for row in rrset:
                        nsDict[name].append(row.address)
                        hasAuthorityIp = True
            nameServers = nsDict

        result = []
        ttl = None
        # in case of answer returns CNAME:
        for rrset in ans.response.answer:
            if rrset.rdtype == rdatatype.CNAME:
                hasCNAME = True
                tmpRes, ttl = self.query(
                    rrset[0].to_text(), rdtype, self.queryRoot(), True)
                result.append(rrset)
                result += tmpRes

        # if authority is present and cname not present, use same domain name to query
        if not hasCNAME and hasAuthority:
            if hasAuthorityIp:
                result, ttl = self.query(domain, rdtype, nameServers)
            else:
            # If no nameservers ip is provided in additional or last query, query and try them one by one
                for name in nameServers:
                    nameServerList = []
                    nameServerRes, _ = self.query(
                        name, rdatatype.A, self.queryRoot(), True)
                    for rrset in nameServerRes:
                        if rrset.rdtype == rdatatype.A or rrset.rdtype == rdatatype.AAAA:
                            for row in rrset:
                                nameServerList.append(row.address)
                    if len(nameServerList) != 0:
                        try:
                            result, ttl = self.query(domain, rdtype, {name:nameServerList})
                        except dns.exception.DNSException as e:
                            print(e)
                    if result is not None:
                        break

        # if it's the first query(at the bottom of stack) to a domain name, write result to cache
        if writeCache and ttl is not None:
            self.cache.writeCache(cacheKey, result, ttl)

        return result, ttl

    def queryRoot(self) -> Dict[str, List[str]]:
        """
        Query IP address and name of root DNS server.
        If cache is present, return address from cache.
        """

        result = self.cache.readCache("root")
        if result is not None:
            return result[0]

        answer = self.resolve("", rdatatype.NS, ["8.8.8.8"])

        # Get ip from all root servers
        rootServers: Dict[str, List[str]] = {}
        for row in answer:
            try:
                answer = self.resolve(
                    row.target, rdatatype.A, ["8.8.8.8"], True)
                rootServers[row.target.to_text()] = [
                    row.address for row in answer]
            except resolver.NoNameservers or resolver.NoAnswer:
                pass

        self.cache.writeCache("root", rootServers, answer.rrset.ttl)

        return rootServers
