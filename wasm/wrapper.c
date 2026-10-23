#include <errno.h>
#include "bsdconv.h"

_Static_assert(sizeof(struct data_st) == 12, "binary codec data layout");
_Static_assert(sizeof(struct state_st) == 16, "binary codec state layout");

/* The caller owns the returned buffer and releases it with bsdconv_free(). */
char *chicomp_convert(const char *chain, const char *input, int strict) {
    struct bsdconv_instance *ins = bsdconv_create(chain);
    if (!ins) return NULL;
    bsdconv_init(ins);
    ins->output_mode = BSDCONV_AUTOMALLOC;
    ins->output.len = 1;
    ins->input.data = (void *)input;
    ins->input.len = strlen(input);
    ins->input.flags = 0;
    ins->input.next = NULL;
    ins->flush = 1;
    bsdconv(ins);
    char *out = ins->output.data;
    int failed = strict && (*ins->ierr || *ins->oerr);
    if (out) out[ins->output.len] = 0;
    bsdconv_destroy(ins);
    if (failed) {
        free(out);
        errno = EILSEQ;
        return NULL;
    }
    return out;
}
