from hashlib import blake2b, md5


def hash_data(data):
    if not isinstance(data, bytes):
        data = data.encode()
    return md5(data).hexdigest()


if __name__ == "__main__":
    data = """                    if h_data != self._last_hash_clip_data:
                        self.this_clip.set_to_clip(clip_data.data)
                        self._last_hash_clip_data = h_data
                        sync_sample = clip_data.data[:1000]"""
    print(hash_data(data))
    data = b"""                    if h_data != self._last_hash_clip_data:
                        self.this_clip.set_to_clip(clip_data.data)
                        self._last_hash_clip_data = h_data
                        sync_sample = clip_data.data[:1000]"""
    print(hash_data(data))

