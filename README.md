# Musicode：基于 C 的音乐编程语言

小组成员：何逸宸 ZY2106342  梁世俊 ZY2106323

**希望进行申优及课堂展示**

编程语言说明：见`musicode.pdf`

编译器运行：

1. 安装python依赖

   pip install -r requirements.txt

2. 将 lilypond-2.23.5-1.mingw.exe 所在路径加入环境变量(用于生成五线谱)

3. 运行代码，在musicode文件夹所在路径

   python -m musicode musicode/test.mc

   控制台输出中间代码及语法树

   生成 `可播放的midi文件：temp.mid` 以及 `五线谱`

