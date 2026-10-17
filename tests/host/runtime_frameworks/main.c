#include "framework_layout.h"
#include <assert.h>

int main(void)
{
    char name[128], path[1024];
    assert(pg_framework_name("ec", "ntdll.dll", name, sizeof(name)));
    assert(!strcmp(name, "PGEC_ntdll_dll"));
    assert(pg_framework_name("a64", "NTDLL.DLL", name, sizeof(name)));
    assert(!strcmp(name, "PGA64_ntdll_dll"));
    assert(pg_framework_path("/app/Frameworks", "test", "Spike-ARM64EC", path, sizeof(path)));
    assert(!strcmp(path, "/app/Frameworks/PGTest_spike_arm64ec.framework/PGTest_spike_arm64ec"));
    assert(!pg_framework_name("ec", "../ntdll", name, sizeof(name)));
    assert(!pg_framework_name("ec", "a\\b", name, sizeof(name)));
    assert(!pg_framework_name("ec", "", name, sizeof(name)));
    assert(!pg_framework_name("bad", "ntdll.dll", name, sizeof(name)));
    assert(!pg_framework_name("ec", "ntdll.dll", name, 5));
    assert(!pg_framework_path("/app/Frameworks", "ec", "ntdll.dll", path, 10));
    puts("Framework loader path checks passed");
    return 0;
}
