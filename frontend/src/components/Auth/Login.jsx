import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'
import AuthLayout, { Field } from './AuthLayout'
import { Spinner } from '../Common/ui'

const Login = () => {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [form, setForm] = useState({ username: '', password: '' })
  const [loading, setLoading] = useState(false)

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const onSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await login(form)
      navigate('/')
    } catch {
      // toast shown by the API client
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      title="Welcome back"
      subtitle="Sign in to continue where you left off."
      footer={<>New here? <Link to="/register" className="link-gold">Create an account</Link></>}
    >
      <form onSubmit={onSubmit} className="space-y-5">
        <Field label="Username" name="username" value={form.username} onChange={onChange}
          autoComplete="username" placeholder="your-username" required />
        <Field label="Password" name="password" type="password" value={form.password} onChange={onChange}
          autoComplete="current-password" placeholder="••••••••" minLength={8} required
          hint="Account from before passwords existed? Choose one now (8+ characters) to claim it." />
        <button type="submit" disabled={loading} className="btn-primary w-full py-3">
          {loading ? <Spinner /> : <>Sign in <ArrowRight className="h-4 w-4" /></>}
        </button>
      </form>
    </AuthLayout>
  )
}

export default Login
