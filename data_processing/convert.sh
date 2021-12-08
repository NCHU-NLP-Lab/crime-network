#!/bin/bash

function process() {
    cd "../raw-data" || exit
    ls -1 "${1}"> "${1}list"
    split -l 25000 "${1}list" "${1}seg"
    rm "${1}list"
    cd "${1}" || exit
    for f in "../${1}"seg*;
    do
        printf "processing:\t${f}\n"
        cat $(grep -v '^#' "${f}") >> "../../combined/${1}.jsonl"
        printf "done:\t${f}\n"
    done;
    cd ..
    rm "${1}seg"*
    cd "../combined" || exit
}

# process 臺灣高等法院臺南分院

process 臺灣臺北地方法院
process 臺灣高等法院

process 臺灣南投地方法院
process 臺灣嘉義地方法院
process 臺灣基隆地方法院
process 臺灣士林地方法院
process 臺灣宜蘭地方法院
process 臺灣屏東地方法院
process 臺灣彰化地方法院
process 臺灣新北地方法院
process 臺灣新竹地方法院
process 臺灣桃園地方法院
process 臺灣橋頭地方法院
process 臺灣澎湖地方法院
process 臺灣臺中地方法院
process 臺灣臺南地方法院
process 臺灣臺東地方法院
process 臺灣花蓮地方法院
process 臺灣苗栗地方法院
process 臺灣雲林地方法院
process 臺灣高等法院臺中分院
process 臺灣高等法院花蓮分院
process 臺灣高等法院高雄分院
process 臺灣高雄地方法院
process 臺灣高雄少年及家事法院
