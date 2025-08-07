export default function Layout({ children }) {
  return (
    <div className="min-w-screen min-h-screen bg-gray-100 flex justify-center">
      <div className="w-2/3 bg-white rounded-2xl shadow-lg p-6 my-4">
        {children}
      </div>
    </div>
  )
}
