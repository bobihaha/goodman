/**
 * 数据格式化工具函数
 */

import dayjs from 'dayjs'
import customParseFormat from 'dayjs/plugin/customParseFormat'

dayjs.extend(customParseFormat)

function parseDateValue(date: string | Date | null | undefined) {
  if (!date) return null

  if (date instanceof Date) {
    const parsed = dayjs(date)
    return parsed.isValid() ? parsed : null
  }

  const parsed = dayjs(date)
  if (parsed.isValid()) return parsed

  const fallbackFormats = [
    'YY/M/D',
    'YY/MM/DD',
    'YYYY/M/D',
    'YYYY/MM/DD',
    'YYYY-M-D',
    'YYYY-MM-DD',
    'YYYY/M/D HH:mm:ss',
    'YYYY/MM/DD HH:mm:ss',
    'YY/M/D HH:mm:ss',
    'YY/MM/DD HH:mm:ss'
  ]

  for (const format of fallbackFormats) {
    const fallbackParsed = dayjs(date, format, true)
    if (fallbackParsed.isValid()) {
      return fallbackParsed
    }
  }

  return null
}

function hasExplicitTime(date: string | Date | null | undefined): boolean {
  if (date instanceof Date) return true
  if (typeof date !== 'string') return false
  return /[T\s]\d{1,2}:\d{2}/.test(date)
}

/**
 * 格式化日期为 YY/M/D 格式
 */
export function formatDateShort(date: string | null | undefined): string {
  if (!date) return '-'
  
  const parsed = parseDateValue(date)
  if (!parsed) return '-'
  
  return parsed.format('YY/M/D')
}

/**
 * 格式化日期为 YYYY-MM-DD 格式
 */
export function formatDate(date: string | null | undefined): string {
  if (!date) return '-'
  
  const parsed = parseDateValue(date)
  if (!parsed) return '-'
  
  return parsed.format('YYYY-MM-DD')
}

/**
 * 格式化日期时间
 */
export function formatDateTime(date: string | null | undefined): string {
  if (!date) return '-'
  
  const parsed = parseDateValue(date)
  if (!parsed) return '-'

  if (!hasExplicitTime(date)) {
    return parsed.format('YYYY-MM-DD')
  }
  
  return parsed.format('YYYY-MM-DD HH:mm:ss')
}

/**
 * 格式化流量大小（MB转换为GB）
 */
export function formatFlow(mb: number | null | undefined): string {
  if (mb === null || mb === undefined || isNaN(mb)) return '-'

  if (mb >= 1024) {
    const gb = mb / 1024
    return Number.isInteger(gb) ? `${gb}G` : `${Math.round(gb)}G`
  }

  return `${mb}M`
}

/**
 * 格式化流量用量（保留2位小数）
 */
export function formatFlowValue(mb: number | null | undefined): string {
  if (mb === null || mb === undefined || isNaN(mb)) return '-'

  if (mb >= 1024) {
    return `${(mb / 1024).toFixed(2)}G`
  }

  return `${mb.toFixed(2)}M`
}

/**
 * 格式化流量使用百分比
 */
export function formatUsagePercent(used: number, total: number): number {
  if (!total || total <= 0) return 0

  const percent = (used / total) * 100
  return Number(Math.max(percent, 0).toFixed(2))
}

/**
 * 格式化金额（保留2位小数）
 */
export function formatMoney(amount: number | null | undefined): string {
  if (amount === null || amount === undefined || isNaN(amount)) return '¥0.00'
  
  return `¥${amount.toFixed(2)}`
}

/**
 * 格式化ICCID（显示前6位和后4位）
 */
export function formatICCID(iccid: string | null | undefined): string {
  if (!iccid) return '-'
  
  if (iccid.length >= 10) {
    return `${iccid.substring(0, 6)}****${iccid.substring(iccid.length - 4)}`
  }
  
  return iccid
}

/**
 * 判断日期是否过期
 */
export function isExpired(date: string | null | undefined): boolean {
  if (!date) return false
  
  const parsed = parseDateValue(date)
  if (!parsed) return false
  
  return parsed.isBefore(dayjs(), 'day')
}

/**
 * 计算两个日期之间的天数
 */
export function daysBetween(date1: string, date2: string): number {
  const d1 = dayjs(date1)
  const d2 = dayjs(date2)
  
  if (!d1.isValid() || !d2.isValid()) return 0
  
  return d2.diff(d1, 'day')
}

/**
 * 格式化相对时间（如：3天前、2小时前）
 */
export function formatRelativeTime(date: string | null | undefined): string {
  if (!date) return '-'
  
  const parsed = dayjs(date)
  if (!parsed.isValid()) return '-'
  
  const now = dayjs()
  const diffSeconds = now.diff(parsed, 'second')
  const diffMinutes = now.diff(parsed, 'minute')
  const diffHours = now.diff(parsed, 'hour')
  const diffDays = now.diff(parsed, 'day')
  const diffMonths = now.diff(parsed, 'month')
  const diffYears = now.diff(parsed, 'year')
  
  if (diffSeconds < 60) {
    return '刚刚'
  } else if (diffMinutes < 60) {
    return `${diffMinutes}分钟前`
  } else if (diffHours < 24) {
    return `${diffHours}小时前`
  } else if (diffDays < 30) {
    return `${diffDays}天前`
  } else if (diffMonths < 12) {
    return `${diffMonths}个月前`
  } else {
    return `${diffYears}年前`
  }
}

/**
 * 格式化运营商名称
 */
export function formatCarrier(carrier: string | null | undefined): string {
  if (!carrier) return '-'
  
  const carrierMap: Record<string, string> = {
    'cmcc': '中国移动',
    'cucc': '中国联通',
    'ctcc': '中国电信'
  }
  
  return carrierMap[carrier] || carrier
}

/**
 * 格式化流量大小（formatFlow的别名，用于兼容）
 */
export function formatFlowSize(mb: number | null | undefined): string {
  return formatFlow(mb)
}

/**
 * 格式化百分比（保留2位小数）
 */
export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) return '0%'
  
  return `${value.toFixed(2)}%`
}

/**
 * 格式化数字（添加千分位分隔符）
 */
export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined || isNaN(value)) return '0'
  
  return value.toLocaleString('zh-CN')
}
