from hashlib import blake2b, md5


def hash_data(data):
    if not isinstance(data, bytes):
        data = data.encode()
    return md5(data).hexdigest()


if __name__ == "__main__":
    print(hash_data("""
    slkdjflskdjlf
        lskdjflskjdlf 
        sldkjflsdkjfl
        
        了开始简单立法空间是老师打开基辅罗斯大家
        
        
        率领打开基辅罗斯的激发l
        
        老师的基辅罗斯的空间
    
    """))
