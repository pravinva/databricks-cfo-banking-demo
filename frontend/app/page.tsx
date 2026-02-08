export default function Home() {
  return (
    <div className="min-h-screen flex items-center justify-center p-8">
      <div className="max-w-2xl w-full">
        <h1 className="text-2xl font-semibold mb-2">Deprecated frontend</h1>
        <p className="text-sm opacity-80">
          This <code>frontend/</code> app is not used. The canonical UI is <code>frontend_app/</code> and is deployed via
          Databricks Apps.
        </p>
      </div>
    </div>
  )
}
