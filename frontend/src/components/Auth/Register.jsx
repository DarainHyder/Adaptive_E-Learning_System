import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowRight } from 'lucide-react'
import { useAuth } from '../../hooks/useAuth'
import AuthLayout, { Field } from './AuthLayout'
import { Spinner } from '../Common/ui'

const STYLES = [
  ['mixed', 'A bit of everything'],
  ['visual', 'Visual — diagrams & examples'],
  ['reading', 'Reading — detailed explanations'],
  ['kinesthetic', 'Hands-on — coding exercises'],
]

const Register = () => {
  const navigate = useNavigate()
  const { register } = useAuth()
  const [form, setForm] = useState({ username: '', email: '', password: '', learning_style: 'mixed' })
  const [loading, setLoading] = useState(false)

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const onSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await register(form)
      navigate('/')
    } catch {
      // toast shown by the API client
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      title="Create your account"
      subtitle="Two minutes to set up. The system calibrates to you as you go."
      footer={<>Already have an account? <Link to="/login" className="link-gold">Sign in</Link></>}
    >
      <form onSubmit={onSubmit} className="space-y-5">
        <Field label="Username" name="username" value={form.username} onChange={onChange}
          autoComplete="username" placeholder="ada" pattern="[A-Za-z0-9_.\-]{3,40}"
          title="3-40 letters, numbers, _ . -" required />
        <Field label="Email" name="email" type="email" value={form.email} onChange={onChange}
          autoComplete="email" placeholder="ada@example.com" required />
        <Field label="Password" name="password" type="password" value={form.password} onChange={onChange}
          autoComplete="new-password" placeholder="At least 8 characters" minLength={8} required />
        <Field label="How do you learn best?">
          <select name="learning_style" value={form.learning_style} onChange={onChange} className="input-field">
            {STYLES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
          </select>
        </Field>
        <button type="submit" disabled={loading} className="btn-primary w-full py-3">
          {loading ? <Spinner /> : <>Create account <ArrowRight className="h-4 w-4" /></>}
        </button>
      </form>
    </AuthLayout>
  )
}

export default Register
