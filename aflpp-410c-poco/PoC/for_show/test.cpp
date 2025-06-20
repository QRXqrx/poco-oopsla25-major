#include<bits/stdc++.h>

int main() {
	char str[100];
	scanf("%s",str);
	
	if(strlen(str)<5){
		return 0;
	}
	
	if(strlen(str)>99){
		abort();
	}
	
	if(str[0]=='h'){
		if(str[1]=='e'){
			if(str[2]=='l'){
				if(str[3]=='l'){
					if(str[4]=='o'){
						printf("bug triggered");
					}
				}
			}
		}
	}
	
}