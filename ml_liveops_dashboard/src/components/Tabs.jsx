import { NavLink } from 'react-router-dom'

export default function Tabs() {
    const tabs = [
        { name: 'Tutorials', path: '/' },
        { name: 'Simulations', path: '/simulations' },
    ]

  return (
        <div className="flex space-x-4 border-b border-gray-200 mb-6">
        {tabs.map((tab) => (
            <NavLink
            key={tab.name}
            to={tab.path}
            end
            className={({ isActive }) =>
                `px-4 py-2 rounded-t-lg font-medium ${
                isActive
                    ? 'bg-white shadow-md text-blue-600'
                    : 'text-gray-600 hover:text-blue-500'
                }`
            }
            >
            {tab.name}
            </NavLink>
        ))}
        </div>
    )
}
