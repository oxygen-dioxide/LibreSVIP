��    &      L              |     }  ^   �     �      �  	     >       [     r     �     �     �  .   �     �       E     T   b  0   �     �  H   �     :     O     f  H  o  +   �     �  �   �  B   �  _   $	     �	     �	  <   �	  !   �	     �	     
     <
    \
  �   t  �  P     �  \   �     E     R     q  !  x     �  *   �  *   �            3   &     Z     g  Q   �  T   �  6   '     ^  W   e     �     �  	   �    �             �   5  Q   �  G   F     �     �  ?   �  !   �          ,     B  �   [  �   :   All kept All notes will be set to 0 vibrato depth to ensure the output pitch curve is the same as input All removed Always follow instant pitch mode Cantonese Conversion plugin for Synthesizer V Studio project file, it supports reading and writing of all parameters including notes, lyrics, parameter curve, note attributes, note group, and instant pitch mode.
Notes: Importing a project file with overlapping notes is undefined behavior that can lead to unforeseen exceptions. Convert to breath mark Edited part only (plain mode) Edited part only (vibrato mode) English Full pitch curve Generate a track for each note group reference Hybrid mode Ignore all breath notes Input the edited part of pitch curve; default vibrato will be ignored Input the edited part of pitch curve; default vibrato will be imported if not edited Input the full pitch curve regardless of editing Japanese Keep all notes' default vibrato, but may cause inconsistent pitch curves Keep as normal notes Keep original position Mandarin Notice: If there are too many note groups, please choose "Keep original position" to avoid excessive track count. But if there are notes that are adjacent (but not overlapped) between note groups or between note groups and main group, it is recommended to choose "Split to tracks" to ensure the paragraph division is not broken. Override default language for the voicebank Pitch input mode Reduce the sampling interval to improve the accuracy of parameter curves, but may cause rendering lag (e.g. Synthesizer V Studio Pro + AI voicebank). Please set this value according to your hardware configuration and actual experience. Remove vibrato in edited part, keep default vibrato in other parts Set the average sampling interval of parameter points to improve performance (0 means no limit) Spanish Split all to tracks Split note groups to separate tracks only when notes overlap Synthesizer V Studio project file The way to handle breath notes The way to handle note groups The way to handle vibrato notes This option controls the range of pitch curve to be imported and the judgment condition. The definition of "edited part" is: the pitch deviation in the parameter panel, the pitch transition in the vibrato envelope and the pitch transition in the note properties have been edited. When this option is turned off, the default pitch curve will always be imported regardless of the project setting. If you have tuned the pitch curve based on instant pitch mode, it is recommended to turn on this option. Project-Id-Version:  libresvip
Report-Msgid-Bugs-To: EMAIL@ADDRESS
POT-Creation-Date: 2024-06-30 09:21+0000
PO-Revision-Date: 2024-06-29 03:33+0000
Last-Translator: FULL NAME <EMAIL@ADDRESS>
Language: zh_CN
Language-Team: Chinese Simplified
Plural-Forms: nplurals=1; plural=0;
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.15.0
 全部保留 所有音符的颤音深度将被设置为 0，以保证输出的音高曲线与输入一致 全部抹平 遵循即时音高模式设置 粤语 Synthesizer V Studio 工程格式转换插件，支持包括曲谱、歌词、参数曲线、音符属性、音符组、即时音高模式在内所有数据的读取与写入。
请注意：输入带有重叠音符的工程文件是未定义的行为，可能导致无法预料的异常。 转换为换气标记 仅输入已编辑部分（平整模式） 仅输入已编辑部分（颤音模式） 英语 输入完整音高曲线 为每个音符组引用生成一个单独的音轨 混合保留 忽略所有换气音符 仅输入已编辑部分的音高曲线；未经编辑的默认颤音将被忽略 仅输入已编辑部分的音高曲线；未经编辑的默认颤音也将被导入 不论是否经过编辑，均输入整条音高曲线 日语 保持所有音符的默认颤音，但可能造成输入与输出音高曲线不一致 保留为普通音符 保留原始位置 普通话 注意：若音符组较多，请尽量选择“保留原始位置”以防止轨道数量暴增。但若音符组之间、音符组与主组之间存在时间轴上紧挨 (但不重叠) 的音符，则建议选择“拆分为轨道”以确保段落划分不被破坏。 指定声库的默认语种 音高信息输入模式 减小采样间隔可提高参数曲线的精准度，但可能造成渲染卡顿（例如 Synthesizer V Studio Pro + AI 声库）。请根据硬件配置与实际体验酌情设置此值。 在输入音高被编辑过的区域去除颤音，其余部分保留默认颤音 设置参数点的平均采样间隔以改善性能（0 为无限制） 西班牙语 全部拆分为轨道 仅在出现音符重叠时将音符组拆分至单独的音轨 Synthesizer V Studio 工程文件 换气音符处理方式 音符组导入方式 自动颤音处理方式 本选项控制音高曲线被导入的范围和判定条件。其中“经过编辑”的定义为：参数面板中的音高偏差、颤音包络和音符属性中的音高转变、颤音中的任意一项经过编辑。 关闭此选项时，无论工程文件是否开启了即时音高模式，都只会考虑原始的默认音高。若您基于即时音高模式进行了调校，建议打开此选项。 