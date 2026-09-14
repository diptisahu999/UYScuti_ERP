/** @odoo-module **/

import * as dateHelpers from "@spreadsheet/global_filters/helpers";
import { serializeDate, serializeDateTime } from "@web/core/l10n/dates";
import { Domain } from "@web/core/domain";

// Patch getRelativeDateDomain
if (!dateHelpers.__patched_uyscuti_dashboard_filter__) {
    const original = dateHelpers.getRelativeDateDomain;
    dateHelpers.getRelativeDateDomain = function (now, offset, rangeType, fieldName, fieldType) {
        let startDate, endDate;
        const offsetParam = { days: offset || 0 };

        switch (rangeType) {
            case "today":
                startDate = now.plus(offsetParam).startOf("day");
                endDate = now.plus(offsetParam).endOf("day");
                break;
            case "yesterday":
                // Yesterday is today - 1 day
                startDate = now.minus({ days: 1 }).plus(offsetParam).startOf("day");
                endDate = now.minus({ days: 1 }).plus(offsetParam).endOf("day");
                break;
            case "this_week":
                startDate = now.plus(offsetParam).startOf("week");
                endDate = now.plus(offsetParam).endOf("week");
                break;
            case "last_week":
                startDate = now.minus({ weeks: 1 }).plus(offsetParam).startOf("week");
                endDate = now.minus({ weeks: 1 }).plus(offsetParam).endOf("week");
                break;
            case "this_month":
                startDate = now.plus(offsetParam).startOf("month");
                endDate = now.plus(offsetParam).endOf("month");
                break;
            case "last_month":
                startDate = now.minus({ months: 1 }).plus(offsetParam).startOf("month");
                endDate = now.minus({ months: 1 }).plus(offsetParam).endOf("month");
                break;
            case "this_quarter":
                startDate = now.plus(offsetParam).startOf("quarter");
                endDate = now.plus(offsetParam).endOf("quarter");
                break;
            case "last_quarter":
                startDate = now.minus({ quarters: 1 }).plus(offsetParam).startOf("quarter");
                endDate = now.minus({ quarters: 1 }).plus(offsetParam).endOf("quarter");
                break;
            case "this_year":
                startDate = now.plus(offsetParam).startOf("year");
                endDate = now.plus(offsetParam).endOf("year");
                break;
            case "last_year":
                startDate = now.minus({ years: 1 }).plus(offsetParam).startOf("year");
                endDate = now.minus({ years: 1 }).plus(offsetParam).endOf("year");
                break;
            default:
                // Fallback to original for standard types or undefined
                if (original) {
                    return original(now, offset, rangeType, fieldName, fieldType);
                }
                return undefined;
        }

        if (startDate && endDate) {
            const leftBound = fieldType === "date" ? serializeDate(startDate) : serializeDateTime(startDate);
            const rightBound = fieldType === "date" ? serializeDate(endDate) : serializeDateTime(endDate);
            return new Domain(["&", [fieldName, ">=", leftBound], [fieldName, "<=", rightBound]]);
        }
    };
    dateHelpers.__patched_uyscuti_dashboard_filter__ = true;
}
