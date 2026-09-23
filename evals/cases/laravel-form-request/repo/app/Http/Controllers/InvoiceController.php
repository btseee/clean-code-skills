<?php

namespace App\Http\Controllers;

use App\Models\Invoice;
use Illuminate\Http\Request;

class InvoiceController extends Controller
{
    public function store(Request $request)
    {
        if ($request->user()->role !== 'accountant') {
            abort(403);
        }

        $validated = $request->validate([
            'amount' => 'required|numeric|min:0.01',
            'due_date' => 'required|date|after:today',
        ]);

        $invoice = Invoice::create($validated);

        return response()->json($invoice, 201);
    }
}
