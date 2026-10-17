/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef POCKETGAMES_FRAMEWORK_LAYOUT_H
#define POCKETGAMES_FRAMEWORK_LAYOUT_H
#include <stddef.h>
#include <stdio.h>
#include <string.h>

/* Shared by Wine, the app and the host test. Keep in sync with
 * tools/package_runtime_frameworks.py. Collision checks happen at packaging. */
static inline int pg_framework_name(const char *group, const char *module,
                                    char *out, size_t capacity)
{
    const char *prefix;
    size_t used, i;
    if (!strcmp(group, "ec")) prefix = "PGEC_";
    else if (!strcmp(group, "a64")) prefix = "PGA64_";
    else if (!strcmp(group, "test")) prefix = "PGTest_";
    else return 0;
    used = strlen(prefix);
    if (!module || !*module || strlen(module) > 100 || capacity <= used) return 0;
    memcpy(out, prefix, used);
    for (i = 0; module[i]; i++)
    {
        unsigned char c = (unsigned char)module[i];
        if (c >= 'A' && c <= 'Z') c += 'a' - 'A';
        if (c == '.' || c == '-') c = '_';
        if (!((c >= 'a' && c <= 'z') || (c >= '0' && c <= '9') || c == '_') || used + 1 >= capacity)
            return 0;
        out[used++] = (char)c;
    }
    out[used] = 0;
    return 1;
}

static inline int pg_framework_path(const char *root, const char *group, const char *module,
                                    char *out, size_t capacity)
{
    char name[128];
    int length;
    if (!root || !*root || !pg_framework_name(group, module, name, sizeof(name))) return 0;
    length = snprintf(out, capacity, "%s/%s.framework/%s", root, name, name);
    return length > 0 && (size_t)length < capacity;
}
#endif
