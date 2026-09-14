/** @odoo-module **/

import * as dateHelpers from "@spreadsheet/global_filters/helpers";
import { serializeDate, serializeDateTime } from "@web/core/l10n/dates";
import { Domain } from "@web/core/domain";

// Patch getRelativeDateDomain to support "today"
if (!dateHelpers.__patched_today_relative_range__) {
  const original = dateHelpers.getRelativeDateDomain;
  dateHelpers.getRelativeDateDomain = function (
    now,
    offset,
    rangeType,
    fieldName,
    fieldType
  ) {
    if (rangeType === "today") {
      const offsetParam = { days: offset || 0 };
      const startDate = now.startOf("day").plus(offsetParam);
      const endDate = now.endOf("day").plus(offsetParam);
      const leftBound =
        fieldType === "date"
          ? serializeDate(startDate)
          : serializeDateTime(startDate);
      const rightBound =
        fieldType === "date"
          ? serializeDate(endDate)
          : serializeDateTime(endDate);
      return new Domain([
        "&",
        [fieldName, ">=", leftBound],
        [fieldName, "<=", rightBound],
      ]);
    }
    return original
      ? original(now, offset, rangeType, fieldName, fieldType)
      : undefined;
  };
  dateHelpers.__patched_today_relative_range__ = true;
}
