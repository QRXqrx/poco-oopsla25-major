#!/bin/bash

# 确保传入了目录参数
if [ $# -ne 1 ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

DIR="$1"
SUM=0
COUNT=0

# 遍历目录下所有编号的文件夹
for folder in "$DIR"/*; do
    if [ -d "$folder" ]; then
        # 进入该文件夹
        cd "$folder" || continue

        # 解压 ball.tar
        if [ -f "ball.tar" ]; then
            tar -xf ball.tar
        else
            echo "Warning: $folder/ball.tar not found, skipping..."
            cd - > /dev/null
            continue
        fi

        # 查找 findings/default/plot_data 文件
        PLOT_DATA="findings/default/plot_data"
        if [ -f "$PLOT_DATA" ]; then
            # 获取最后一行
            LAST_LINE=$(tail -n 1 "$PLOT_DATA")
            # 提取最后一个数字（去掉逗号，只保留数值）
            LAST_NUM=$(echo "$LAST_LINE" | awk -F '[ ,%]+' '{print $(NF)}')

            # 确保是一个数字
            if [[ "$LAST_NUM" =~ ^[0-9]+(\.[0-9]+)?$ ]]; then
                SUM=$(echo "$SUM + $LAST_NUM" | bc -l)
                COUNT=$((COUNT + 1))
            else
                echo "Warning: No valid number found in $PLOT_DATA"
            fi
        else
            echo "Warning: $folder/$PLOT_DATA not found"
        fi

        # 回到原目录
        cd - > /dev/null
    fi
done

# 计算平均值
if [ "$COUNT" -gt 0 ]; then
    AVG=$(echo "$SUM / $COUNT" | bc -l)
    echo "Average: $AVG"
else
    echo "No valid numbers found."
fi
