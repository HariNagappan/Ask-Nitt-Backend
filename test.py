import bisect

n=int(input())
vivek=list(map(int,input().split(" ")))
nisha=list(map(int,input().split(" ")))
lst=[vivek[i] - nisha[i] for i in range(n)]
lst.sort()
final=0
for i in range(n):
    tmp=bisect.bisect_right(lst,-lst[i],lo=i+1)
    final+=n-tmp
print(final)