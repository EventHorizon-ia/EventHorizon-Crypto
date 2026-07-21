import { Suspense } from 'react';
import { CheckoutForm } from './CheckoutForm';

export default function CheckoutPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-[#080c14] flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-2 border-cyan-500 border-t-transparent" /></div>}>
      <CheckoutForm />
    </Suspense>
  );
}