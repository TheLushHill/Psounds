//交换数组中两个元素的位置
export function moveToHead(Array, index) {
    Array.unshift(Array.splice(index, 1)[0]);
}