# coding=utf-8
import socket
import sys
import threading
import time
import multiprocessing
import re
import socks
import requests
import os

# ConnectTarget函数递归控制
DG = 0


def getIpFile(type, ip=None, port=None):
    """
    将新的代理IP写入到文件中

    或将文件中IP提取出来
    """

    # 真为写，假为读
    if type:
        iplib = open("ip.txt", "w+", encoding='utf-8')
        iplib.write(str(int(time.time())) + "\n")
        iplib.write(str(ip) + "\n")
        iplib.write(str(port) + "\n")
        iplib.close()
        return
    else:
        # 当文件没有内容时返回False
        if not os.path.getsize("ip.txt") > 2:
            return False

        iplib = open("ip.txt", "r", encoding='utf-8')
        ztime = iplib.readline().split("\n")[0]
        ip = iplib.readline().split("\n")[0]
        port = iplib.readline().split("\n")[0]
        iplib.close()
        return (int(ztime), (ip, int(port)))


def Iplive(ip, port):
    """
    判断代理是否存活
    """
    url = "http://www.qq.com"
    proxies = "http://" + ip + ":" + str(port)
    try:
        data = requests.get(url=url, proxies={'http': proxies}, timeout=2)
        if data.status_code:
            return True
        else:
            return False
    except:
        print("\033[1;31;31m该代理地址 {}:{} 无法使用\033[0m".format(ip, port))
        return False


def getProxyIP(url, type=None):
    """
    获取代理iP，每次只获取一个！
    """
    global DG

    # 获取IP
    try:
        data = requests.get(url, timeout=5)
        if not data.status_code:
            print("无法获取代理IP，错误1!")
            exit(0)
    except:
        print(url, end='')
        print("无法获取代理IP，错误2!")
        exit(0)

    # 根据长度判断代理IP的格式是否正确
    data = data.text
    if len(data) > 20:
        print("无法获取代理IP，错误3!")
        exit(0)

    ip = re.search(".*:", data).group()[0:-1]
    port = re.search(":.*", data).group()[1:]

    # 检查代理IP是否存活,递归三次,然后重置DG变量
    tmp = Iplive(ip, port)
    if not tmp:
        if DG < 3:
            DG = DG + 1
            print("\033[1;31;31m第 {} 次获取新的代理地址效\033[0m".format(DG))
            # print("第 {} 次获取新的代理地址".format(DG))
            return getProxyIP(url)
        else:
            if not tmp:
                print("\033[1;31;31m重新检测了三次新的代理IP, 均无法连通网络，请检查代理是否有效\033[0m")
                # print("重新检测了三次新的代理IP, 均无法连通网络，请检查代理是否有效！")
                exit(1)

            DG = 0

    # 将IP存入到数组中
    # iplib[0] = int(time.time())
    # iplib[1] = (ip, int(port))

    getIpFile(True, ip, port)

    return (ip, int(port))


def getOidIp(url, timeout):
    """

    """

    tmp = getIpFile(False)

    if tmp:
        ntime = time.time()
        ztime = ntime - int(tmp[0])

        if ztime <= timeout:
            print("库存IP")
            return tmp[1]
        else:
            print("过时IP")
            return (getProxyIP(url))

    else:
        print("首次新的")
        return (getProxyIP(url))


def getHost(host):
    """
    获取host字段，返回host、PORT和连接协议类型
    """
    try:
        host = host.decode("utf-8")
        Urlhost = re.search("Host: .*\r\n", host)

        # 判断是否是https
        ifssl = re.match("CONNECT", host)
        if ifssl:
            ifssl = 1
        else:
            ifssl = 0
    except:
        exit(0)

    if Urlhost:
        try:
            Urlhost = Urlhost.group()
            Urlhost = Urlhost[6:]
            Urlhost = Urlhost.strip('\r\n')

            tmp = re.search(":.*", Urlhost)
            if tmp:
                Urlhost = re.search(".*:", Urlhost).group()
                Urlhost = Urlhost[0:-1]
                PORT = tmp.group()[1:]
                PORT = int(PORT)
                return (Urlhost, PORT, ifssl)
            else:
                return (Urlhost, 80, ifssl)
        except:
            exit(0)


class bb:
    def __init__(self):

        self.i = 0
        self.cline = None
        self.adder = None
        self.data = None
        self.type = None
        self.server = None
        self.targetHost = None
        self.targetPort = None
        self.proxyIp = None
        self.proxyPort = None

    def closeAll(self):

        if self.cline:
            self.cline.close()
        elif self.server:
            self.server.close()

        self.i = 1
        return 1

    def ConnectTarget(self):
        """
        与服务器建立socket连接
        """
        print("该 {}:{} 地址正通过代理 {}:{} 连接到: '{}:{}'".format(
            self.adder[0], self.adder[1], self.proxyIp, self.proxyPort, self.targetHost, self.targetPort))
        socks.set_default_proxy(
            socks.HTTP, addr=self.proxyIp, port=self.proxyPort)
        socket.socket = socks.socksocket

        try:
            print("进入try")
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.connect((self.targetHost, self.targetPort))
            self.server = server
            print("成功")

            if self.type:
                data = b"HTTP/1.0 200 Connection Established\r\n\r\n"
                self.cline.sendall(data)
            else:
                self.server.sendall(self.data)

            return 1
        except:
            if self.type:
                print("https 连接错误！")
            else:
                print("http 连接错误！")

            print("错误网站：{}:{}".format(self.targetHost, self.targetPort))
            exit(self.closeAll())

    def ToA(self):
        """
        等待接受客户的的数据，然后将数据转到服务。

        客户端不再发送数据就主动断开，应属于正常。
        """

        while True:
            try:
                self.cline.settimeout(15)
                data = self.cline.recv(1024)
                if data:
                    self.server.sendall(data)
                    continue
                else:
                    print("客户端 {}:{} 不再发送数据！".format(
                        self.adder[0], self.adder[1]))
                    return self.closeAll()
            except:
                print("接收客户端数据超时， {}:{} 不再发送数据！".format(
                    self.adder[0], self.adder[1]))
                exit(self.closeAll())

    def ToB(self):
        global DG

        """
        首先客户端发送数据，然后接收服务的数据
        """

        while True:

            if self.i:
                exit(1)

            try:
                self.server.settimeout(6)
                data = self.server.recv(1024)
                if data:
                    self.cline.sendall(data)
                    continue
                else:
                    return self.closeAll()
            except:
                if self.i:
                    exit(1)

                print("服务器 {}:{} 无响应！".format(
                    self.targetHost, self.targetPort))

                if not DG:
                    DG = 1
                    print("换一次IP")
                    tmpProxy = getProxyIP(proxyUrl)

                    # 存入
                    self.proxyIp = tmpProxy[0]
                    self.proxyPort = tmpProxy[1]

                    self.server.close()
                    self.ConnectTarget()

                    t1 = threading.Thread(target=self.ToA)
                    t1.start()
                    self.ToB()
                    exit(1)

                print("换一次ip无效，丢弃这次连接！")
                exit(self.closeAll())


def main(cline, adder, proxyHost):

    # 接收A的初始请求
    cline = cline
    data = cline.recv(4096)

    # 获取服务器的host和port，返回元组，第三位是判断连接协议
    Urlhost = getHost(data)

    obj = bb()
    obj.cline = cline
    obj.adder = adder
    obj.data = data
    obj.targetHost = Urlhost[0]
    obj.targetPort = Urlhost[1]
    obj.type = Urlhost[2]
    obj.proxyIp = proxyHost[0]
    obj.proxyPort = proxyHost[1]

    obj.ConnectTarget()

    t1 = threading.Thread(target=obj.ToA)
    t1.start()
    obj.ToB()


if __name__ == "__main__":
    print("正在初始化....")

    # 代理地址
    proxyUrl = "http://192.168.1.6"

    # 代理超时时间
    timeout = 420

    #
    os.system("echo '' > ip.txt")

    # 初始化套接字
    IP = '0.0.0.0'
    PORT = 8080
    proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    try:
        proxy.bind((IP, PORT))
        proxy.listen(10)
    except:
        print("{} 端口已被占用！".format(PORT))
        exit(0)

    print("初始化完成，监听本地：{}:{}, 等待连接...".format(IP, PORT))
    while True:
        cline, adder = proxy.accept()

        proxyHost = getOidIp(proxyUrl, timeout)

        print("{}:{} 已连接".format(adder[0], adder[1]))
        # 使用多进程
        p = multiprocessing.Process(
            target=main, args=(cline, adder, proxyHost))
        p.start()