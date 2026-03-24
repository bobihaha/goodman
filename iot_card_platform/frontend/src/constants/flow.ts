export const FLOW_PACKAGE_OPTIONS = [
  { label: '1GB', value: 1024 },
  { label: '2GB', value: 2048 },
  { label: '5GB', value: 5120 },
  { label: '10GB', value: 10240 },
  { label: '20GB', value: 20480 },
  { label: '50GB', value: 51200 },
  { label: '100GB', value: 102400 }
] as const

export const FLOW_PACKAGE_VALUE_SET = new Set(
  FLOW_PACKAGE_OPTIONS.map(item => item.value)
)

export const getFlowPackageLabel = (value: number) => {
  return FLOW_PACKAGE_OPTIONS.find(item => item.value === value)?.label || `${value}MB`
}
