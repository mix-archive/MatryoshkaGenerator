# MatryoshkaGenerator

Generator and solver for some matryoshka-like misc challenges. (DubheCTF 2024 "no more taowa" challenge)

> [!TIP]
> 你说得对，但是世界上一共有一千亿道套娃题，却只有一千个 misc 手。如果套娃题决定入侵 CTF，那么每个 misc 手就要做一亿道套娃题。但是出题人不在乎，出题人只在乎他自己

## 题面

黑盒题，服务给出一个 Socket 端口。

会返回生成的 N 轮套娃题的题面，要求解出套娃题的答案。当解出所有套娃题的答案后，会返回 Flag。

### 题目描述

> 各种 Misc 套娃题打得我有点累了。

## 题解

> [!NOTE]
> 这道题是受到 @zysgmzb 师傅的的 [taowa-gnerator](https://github.com/zysgmzb/taowa-generator) 启发而制作的。
> 出的时候没有意识到这个题目的精神污染性质，给各位被折磨的 Misc 师傅磕头了

总共实现了以下几种娃：

```python
dolls_registry = (
    (Base16Doll, Base32Doll, Base64Doll, Base85Doll), # Base系列编码，随机选择一种
    (RGBAImageBytesDoll,), # 字节编码成 RGBA 图片
    (BitReverseDoll, ByteReverseDoll), # 位翻转和字节翻转
    (WeakZipDoll,), # 弱密码ZIP
    (QRCodeDoll,), # 字符串编码成二维码
    (MostSignificantByteDoll, LeastSignificantByteDoll), # 隐写LSB/MSB
)
```

生成逻辑是上面每行的娃随机选择一个，然后打乱顺序递归生成结果。如果生成的结果超过当前娃的最大承载长度，就将这个娃和上一个娃交换位置，然后重新生成。（具体逻辑见 [encode.py](./src/matryoshka/encode.py)）

其中，QRCodeDoll 会生成一个二维码图片，由于二维码我没有找到可靠的办法来承载二进制，所以它实际上存储的是 Base64 编码的二进制数据。

另外，对于 RGBAImageBytesDoll、MostSignificantByteDoll 和 LeastSignificantByteDoll，由于存储的数据长度可能不足容量，所以存储的前四字节为大端序的数据长度。

此外，WeakZipDoll 生成的密码选择在五位数字的原因是因为这是在我的机器上 Python 多进程能在 60 秒内稳定破解的最长密码（有考虑过六位数字，但是不能稳定破解，可能需要写 C binding，感觉有点麻烦就放弃了）。

解题脚本见 [solve.py](./solve.py)，其中具体实现的逻辑是对于输入的特征选择尝试解码的娃，如果解码成功但是结果不清晰就递归解码，直到解码成功且结果清晰（或者持续解码但是直到低于最小可能长度仍然无法解码就失败）；如果解码失败就尝试下一个娃。
