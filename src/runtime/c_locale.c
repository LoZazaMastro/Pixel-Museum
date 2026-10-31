// Pixel Museum - Process-local C numeric locale for the JSON runtime.
// Copyright (C) 2026 Andrea.
// SPDX-License-Identifier: GPL-3.0-or-later
#include <locale.h>
#include <limits.h>
#include <errno.h>
#include <string.h>
#include <xlocale.h>

/* HarfBuzz's numeric variation parser asks for a C locale explicitly. This
 * application uses C numeric formatting throughout; no locale object is
 * allocated or exposed to the console's uninitialised locale internals. */
static unsigned char museum_c_locale;
locale_t newlocale(int mask, const char *name, locale_t base)
{
    (void)mask; (void)base;
    if (!name || (strcmp(name,"C")!=0 && strcmp(name,"POSIX")!=0)) {
        errno=ENOENT; return (locale_t)0;
    }
    return (locale_t)&museum_c_locale;
}
locale_t uselocale(locale_t locale)
{
    if (locale && locale!=(locale_t)&museum_c_locale && locale!=LC_GLOBAL_LOCALE) {
        errno=EINVAL; return (locale_t)0;
    }
    return (locale_t)&museum_c_locale;
}
int freelocale(locale_t locale)
{
    (void)locale;
    return 0;
}

/* The freestanding entry point does not run the desktop locale bootstrap.
 * Supply the complete C locale in this app rather than requiring that state
 * from the console libc before settings or metadata are parsed. */
struct lconv *localeconv(void)
{
    static char decimal[] = ".";
    static char empty[] = "";
    static struct lconv locale = {
        .decimal_point = decimal, .thousands_sep = empty, .grouping = empty,
        .int_curr_symbol = empty, .currency_symbol = empty,
        .mon_decimal_point = empty, .mon_thousands_sep = empty, .mon_grouping = empty,
        .positive_sign = empty, .negative_sign = empty,
        .int_frac_digits = CHAR_MAX, .frac_digits = CHAR_MAX,
        .p_cs_precedes = CHAR_MAX, .p_sep_by_space = CHAR_MAX,
        .n_cs_precedes = CHAR_MAX, .n_sep_by_space = CHAR_MAX,
        .p_sign_posn = CHAR_MAX, .n_sign_posn = CHAR_MAX,
        .int_p_cs_precedes = CHAR_MAX, .int_n_cs_precedes = CHAR_MAX,
        .int_p_sep_by_space = CHAR_MAX, .int_n_sep_by_space = CHAR_MAX,
        .int_p_sign_posn = CHAR_MAX, .int_n_sign_posn = CHAR_MAX
    };
    return &locale;
}
