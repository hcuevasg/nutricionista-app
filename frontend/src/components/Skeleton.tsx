interface SkeletonProps {
  className?: string
}

export function Skeleton({ className = '' }: SkeletonProps) {
  return <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
}

export function SkeletonStatCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="bg-white rounded-lg shadow p-6">
          <Skeleton className="h-3 w-24 mb-3" />
          <Skeleton className="h-8 w-16" />
        </div>
      ))}
    </div>
  )
}

export function SkeletonTableRows({ cols = 4, rows = 5 }: { cols?: number; rows?: number }) {
  return (
    <>
      {[...Array(rows)].map((_, i) => (
        <tr key={i} className="border-b border-border">
          {[...Array(cols)].map((_, j) => (
            <td key={j} className="px-6 py-4">
              <Skeleton className={`h-4 ${j === 0 ? 'w-40' : 'w-24'}`} />
            </td>
          ))}
        </tr>
      ))}
    </>
  )
}

export function SkeletonCard({ lines = 3 }: { lines?: number }) {
  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-3">
      {[...Array(lines)].map((_, i) => (
        <Skeleton key={i} className={`h-4 ${i === 0 ? 'w-48' : i === lines - 1 ? 'w-32' : 'w-full'}`} />
      ))}
    </div>
  )
}
