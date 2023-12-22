# sync-clip

## About

A crow platform clipboard synchronous tool, supports synchronized `text`
and `screenshots (PNG)`, support os system: `Windows`, `Linux`

## Example

![example](https://github.com/yujun2647/sync-clip/raw/main/imgs/example.png)

## Quick Start

### Install

#### From Pypi

```shell
pip install sync-clip
```

#### From repository

* From github

```shell
pip install git+https://github.com/yujun2647/sync-clip.git
```

* From gitee

```shell
pip install git+https://gitee.com/walkerjun/sync-clip.git
```

### Usage

#### Start server

* start server at port: 5000

```shell
sclip -t server -sp 5000
```

#### Start client

assume server ip was `192.168.2.34`

* start a client

use following command in different machines then these machines shall share the
clipboard with each other

```shell
sclip -sh 192.168.2.34 -sp 5000
```
