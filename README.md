# littlechat

## About

A crow platform clipboard synchronous tool, supports synchronized `text`
and `screenshots (PNG)`, support os system: `Windows`, `Linux`

## Example

![example](https://github.com/yujun2647/sync-clip/blob/main/imgs/example.png)

## Quick Start

### Install

#### From repository

#### From Pypi

```shell
pip install sync-clip
```

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

#### Connect with client

* connect server above

```shell
sclip -sp 5000
```
