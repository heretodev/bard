#include<stdio.h>
#include<stdint.h>
#include<string.h>
#include<stdlib.h>

extern const uint64_t bytetable[256];

void chunkify(FILE* input,uint64_t ktarget)
{
	uint64_t rollbuffer[64];
	uint64_t currhash;	
	uint64_t k=(uint64_t)((double)(ktarget)/1.25);
	uint64_t kk=k*k;
	
	memset(rollbuffer,0,sizeof(uint64_t)*64);
	
	//k is an power of 2 where the probability of success is 1/k
	uint64_t Z=~(uint64_t)0;
	
	uint64_t K=Z/kk;
	uint64_t Zk=Z-K;
	uint64_t T=0;

	int currbyte=0;
	for(uint64_t i=0;EOF!=(currbyte=getc(input));i++)
	{
		uint64_t tail=rollbuffer[i & 0x3F];
		currhash ^= tail;
		uint64_t bv=bytetable[currbyte];
		rollbuffer[i & 63]=bv;
		currhash = (((currhash << 1) | currhash >> 63) ^ bv);
		
		if(T < Zk) 
		{
			T+=K;			//Overflow check
		}

		if(currhash < T)
		{
			currhash=0;
			printf("%lu\n",i); //binary?
			memset(rollbuffer,0,sizeof(uint64_t)*64);
			T=0;
		}
	}
}

void print_help(const char* arg0)
{
	printf("usage: %s [-t/--target NUM_BYTES] <filename>\n"
		"\t--target: (int) the number of bytes to target.  Defaults to 2048\n"
		"\t--help: Displays this help method",
		arg0
	); 
}

int main(int argc,const char** argv)
{
	FILE* finput=stdin;
	const char* finput_fn=NULL;
	uint64_t target=2048;
	for(int i=1;i<argc;i++)
	{
		const char* arg=argv[i];
		if(arg[0]!='-')
		{
			finput_fn=argv[++i];
		}
		else
		{
			char ch=arg[1];
			if(ch=='-') ch=arg[2];
			switch(ch)
			{
				case 'h':
				case 'H':
				{
					print_help(argv[0]);
					return 0;
				}
				case 't':
				case 'T':
				{
					target=atoi(argv[++i]);
					break;
				}
				default:
				{
					print_help(argv[0]);
					return -1;
				}
			};
		}
	}
	if(finput_fn)
	{
		finput=fopen(finput_fn,"rb");
		if(!finput)
		{
			printf("Error opening file %s",finput_fn);
			return -1;
		}
	}
	chunkify(finput,target);
	return 0;
}

