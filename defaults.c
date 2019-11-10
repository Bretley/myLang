#include<stdlib.h>
#include<string.h>
typedef struct int_array_struct {
    int numDimensions;
    int numElements;
    int* array;
    int dimensionLength[];
} IntArray;

typedef struct generic_array_header {
    int length;
    void* data;
} GenericArray;

typedef struct string_array_header {
    int length;
    String * data[];
} StringArray;

/* sizeof  IntArray = sizeof(int) + sizeof(int) + sizeof(int)*numDimensions +
 * sizeof(int*)
 */

typedef struct better_string {
    unsigned int length;
    char * string;
} String;
/* sizeof String = sizeof(int) + sizeof(char *) */

void printString(String * s) {
    printf(s->string);
}

void freeStringArray(StringArray * s) {
    int i;
    for (i = 0; i < s->length; i++) {
        freeString((s->Length + i);
    }
    free(s);
}

void freeString(String * s) {
    free(s->string);
    free(s);
}

String * createString(char * string) {
    String * newStr = (String *) malloc(sizeof(String));
    newStr->length = (unsigned int) strlen(string);
    newStr->string = (char *)strdup(string);
    return newStr;
}

int main() {
    String * myString = createString("The word");
    printString(myString);
    freeString(myString);
    return 0;
}
